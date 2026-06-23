from __future__ import annotations

import json
import sqlite3
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

from .p0_models import ApprovalRequest, Engagement, EvidenceRecord, RulesOfEngagement, ScopeTarget
from .p0_policy import canonical_json
from .p0_retention import RetentionPolicy, RetentionResult, redact_for_storage, retention_cutoff
from .runner_simulator import RunnerResult

SCHEMA_VERSION = 3


@dataclass(frozen=True)
class StorageSnapshot:
    tenants: int
    clients: int
    engagements: int
    approvals: int
    jobs: int
    evidence_records: int
    audit_events: int


def _utc_timestamp() -> str:
    return datetime.now(timezone.utc).isoformat()


def _json(data: Any) -> str:
    return canonical_json(redact_for_storage(data))


class P0Storage:
    """Small SQLite persistence boundary for simulator state.

    The storage layer records decisions after runner validation. It does not
    authorize jobs and must never be treated as an execution boundary.
    """

    def __init__(self, path: str | Path = ":memory:"):
        self.path = str(path)
        self._connection: sqlite3.Connection | None = None

    @classmethod
    def default(cls) -> "P0Storage":
        return cls(Path("data") / "masterblaster_p0.sqlite3")

    def connect(self) -> sqlite3.Connection:
        if self._connection is None:
            if self.path != ":memory:":
                Path(self.path).parent.mkdir(parents=True, exist_ok=True)
            self._connection = sqlite3.connect(self.path)
            self._connection.row_factory = sqlite3.Row
            self._connection.execute("PRAGMA foreign_keys = ON")
        return self._connection

    def initialize(self) -> None:
        connection = self.connect()
        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS schema_migrations (
                version INTEGER PRIMARY KEY,
                applied_at TEXT NOT NULL
            );
            """
        )
        current_version = self._current_schema_version(connection)
        if current_version < 1:
            connection.executescript(_MIGRATION_001)
            connection.execute(
                "INSERT INTO schema_migrations(version, applied_at) VALUES (?, ?)",
                (1, _utc_timestamp()),
            )
            current_version = 1
        if current_version < 2:
            connection.executescript(_MIGRATION_002)
            connection.execute(
                "INSERT INTO schema_migrations(version, applied_at) VALUES (?, ?)",
                (2, _utc_timestamp()),
            )
            current_version = 2
        if current_version < 3:
            connection.executescript(_MIGRATION_003)
            connection.execute(
                "INSERT INTO schema_migrations(version, applied_at) VALUES (?, ?)",
                (3, _utc_timestamp()),
            )
        if self._current_schema_version(connection) != SCHEMA_VERSION:
            raise RuntimeError("P0 storage schema version mismatch")
        connection.commit()

    def record_runner_result(self, result: RunnerResult) -> None:
        self.initialize()
        engagement = result.engagement
        connection = self.connect()
        with connection:
            self._upsert_engagement(connection, engagement)
            if result.approval:
                self._insert_approval(connection, result.approval)
            if result.job:
                connection.execute(
                    """
                    INSERT OR REPLACE INTO jobs (
                        job_id, tenant_id, client_id, engagement_id, adapter_id,
                        target, arguments_json, issued_at, expires_at, signature, approval_id,
                        status, decision_reason, decision_message
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        result.job.job_id,
                        result.job.tenant_id,
                        result.job.client_id,
                        result.job.engagement_id,
                        result.job.adapter_id,
                        result.job.target,
                        _json(result.job.arguments),
                        result.job.issued_at.isoformat(),
                        result.job.expires_at.isoformat(),
                        result.job.signature,
                        result.approval.approval_id if result.approval else None,
                        result.status,
                        result.decision.reason_code,
                        result.decision.message,
                    ),
                )
                self._insert_evidence(connection, result.evidence)

            self._insert_audit_event(
                connection,
                engagement=engagement,
                action=f"runner.{result.status}",
                reason_code=result.decision.reason_code,
                details={
                    "job_id": result.job.job_id if result.job else None,
                    "approval_id": result.approval.approval_id if result.approval else None,
                    "approval_state": result.approval.state if result.approval else None,
                    "adapter_id": result.job.adapter_id if result.job else result.approval.adapter_id if result.approval else None,
                    "target": result.job.target
                    if result.job
                    else result.approval.target
                    if result.approval
                    else result.decision.normalized_target,
                    "evidence_ids": [evidence.evidence_id for evidence in result.evidence],
                    "message": result.decision.message,
                },
            )

    def snapshot(self) -> StorageSnapshot:
        self.initialize()
        connection = self.connect()
        return StorageSnapshot(
            tenants=self._count(connection, "tenants"),
            clients=self._count(connection, "clients"),
            engagements=self._count(connection, "engagements"),
            approvals=self._count(connection, "approvals"),
            jobs=self._count(connection, "jobs"),
            evidence_records=self._count(connection, "evidence_records"),
            audit_events=self._count(connection, "audit_events"),
        )

    def apply_retention(
        self,
        policy: RetentionPolicy | None = None,
        now: datetime | None = None,
    ) -> RetentionResult:
        self.initialize()
        policy = policy or RetentionPolicy()
        policy.validate()
        connection = self.connect()
        evidence_cutoff = retention_cutoff(policy.evidence_retention_days, now=now)
        job_cutoff = retention_cutoff(policy.job_retention_days, now=now)
        approval_cutoff = retention_cutoff(policy.approval_retention_days, now=now)
        audit_cutoff = retention_cutoff(policy.audit_retention_days, now=now)

        with connection:
            evidence_deleted = connection.execute(
                """
                DELETE FROM evidence_records
                WHERE job_id IN (
                    SELECT job_id FROM jobs WHERE issued_at < ? OR issued_at < ?
                )
                """,
                (evidence_cutoff, job_cutoff),
            ).rowcount
            jobs_deleted = connection.execute(
                "DELETE FROM jobs WHERE issued_at < ?",
                (job_cutoff,),
            ).rowcount
            approvals_deleted = connection.execute(
                """
                DELETE FROM approvals
                WHERE requested_at < ?
                  AND approval_id NOT IN (
                      SELECT approval_id FROM jobs WHERE approval_id IS NOT NULL
                  )
                """,
                (approval_cutoff,),
            ).rowcount
            audit_events_deleted = connection.execute(
                "DELETE FROM audit_events WHERE created_at < ?",
                (audit_cutoff,),
            ).rowcount

        return RetentionResult(
            approvals_deleted=approvals_deleted,
            jobs_deleted=jobs_deleted,
            evidence_deleted=evidence_deleted,
            audit_events_deleted=audit_events_deleted,
        )

    def list_tenants(self, limit: int = 50) -> list[dict[str, Any]]:
        self.initialize()
        cursor = self.connect().execute(
            """
            SELECT tenant_id, display_name, created_at
            FROM tenants
            ORDER BY created_at DESC
            LIMIT ?
            """,
            (limit,),
        )
        return [dict(row) for row in cursor.fetchall()]

    def list_clients(self, limit: int = 50, tenant_id: str | None = None) -> list[dict[str, Any]]:
        self.initialize()
        query = """
            SELECT client_id, tenant_id, display_name, created_at
            FROM clients
        """
        params: list[Any] = []
        if tenant_id:
            query += " WHERE tenant_id = ?"
            params.append(tenant_id)
        query += " ORDER BY created_at DESC LIMIT ?"
        params.append(limit)
        cursor = self.connect().execute(query, params)
        return [dict(row) for row in cursor.fetchall()]

    def list_engagements(self, limit: int = 50, tenant_id: str | None = None) -> list[dict[str, Any]]:
        self.initialize()
        query = """
            SELECT engagement_id, tenant_id, client_id, scope_json, rules_json, expires_at, updated_at
            FROM engagements
        """
        params: list[Any] = []
        if tenant_id:
            query += " WHERE tenant_id = ?"
            params.append(tenant_id)
        query += " ORDER BY updated_at DESC LIMIT ?"
        params.append(limit)
        cursor = self.connect().execute(query, params)
        rows = [self._row_to_dict(row) for row in cursor.fetchall()]
        for row in rows:
            row["scope"] = row.pop("scope", [])
            row["rules"] = row.pop("rules", {})
        return rows

    def list_jobs(self, limit: int = 50, adapter_id: str | None = None) -> list[dict[str, Any]]:
        self.initialize()
        query = """
            SELECT job_id, tenant_id, client_id, engagement_id, adapter_id, target,
                   issued_at, expires_at, status, decision_reason, decision_message, approval_id
            FROM jobs
        """
        params: list[Any] = []
        if adapter_id:
            query += " WHERE adapter_id = ?"
            params.append(adapter_id)
        query += " ORDER BY issued_at DESC LIMIT ?"
        params.append(limit)
        cursor = self.connect().execute(query, params)
        return [dict(row) for row in cursor.fetchall()]

    def list_audit_events(
        self,
        limit: int = 25,
        action: str | None = None,
        reason_code: str | None = None,
        search: str | None = None,
    ) -> list[dict[str, Any]]:
        self.initialize()
        query = """
            SELECT event_id, tenant_id, engagement_id, action, reason_code, created_at, details_json
            FROM audit_events
        """
        clauses: list[str] = []
        params: list[Any] = []
        if action:
            clauses.append("action = ?")
            params.append(action)
        if reason_code:
            clauses.append("reason_code = ?")
            params.append(reason_code)
        if search:
            clauses.append("details_json LIKE ?")
            params.append(f"%{search}%")
        if clauses:
            query += " WHERE " + " AND ".join(clauses)
        query += " ORDER BY created_at DESC LIMIT ?"
        params.append(limit)
        cursor = self.connect().execute(query, params)
        return [self._row_to_dict(row) for row in cursor.fetchall()]

    def list_evidence(
        self,
        limit: int = 25,
        adapter_id: str | None = None,
        job_id: str | None = None,
        search: str | None = None,
    ) -> list[dict[str, Any]]:
        self.initialize()
        query = """
            SELECT evidence_id, job_id, adapter_id, target, parser_id, tool_version, sha256, content_json
            FROM evidence_records
        """
        clauses: list[str] = []
        params: list[Any] = []
        if adapter_id:
            clauses.append("adapter_id = ?")
            params.append(adapter_id)
        if job_id:
            clauses.append("job_id = ?")
            params.append(job_id)
        if search:
            clauses.append("(target LIKE ? OR sha256 LIKE ? OR evidence_id LIKE ? OR job_id LIKE ?)")
            pattern = f"%{search}%"
            params.extend([pattern, pattern, pattern, pattern])
        if clauses:
            query += " WHERE " + " AND ".join(clauses)
        query += " ORDER BY rowid DESC LIMIT ?"
        params.append(limit)
        cursor = self.connect().execute(query, params)
        return [self._row_to_dict(row) for row in cursor.fetchall()]

    def get_evidence(self, evidence_id: str) -> dict[str, Any] | None:
        self.initialize()
        row = self.connect().execute(
            """
            SELECT evidence_id, job_id, adapter_id, target, parser_id, tool_version, sha256, content_json
            FROM evidence_records
            WHERE evidence_id = ?
            """,
            (evidence_id,),
        ).fetchone()
        return self._row_to_dict(row) if row else None

    def create_tenant(self, tenant_id: str, display_name: str) -> None:
        self.initialize()
        tenant_id = tenant_id.strip()
        display_name = display_name.strip() or tenant_id
        if not tenant_id:
            raise ValueError("tenant_id is required")
        connection = self.connect()
        with connection:
            connection.execute(
                """
                INSERT OR REPLACE INTO tenants(tenant_id, display_name, created_at)
                VALUES (?, ?, ?)
                """,
                (tenant_id, display_name, _utc_timestamp()),
            )

    def create_client(self, client_id: str, tenant_id: str, display_name: str) -> None:
        self.initialize()
        client_id = client_id.strip()
        tenant_id = tenant_id.strip()
        display_name = display_name.strip() or client_id
        if not client_id or not tenant_id:
            raise ValueError("client_id and tenant_id are required")
        connection = self.connect()
        with connection:
            connection.execute(
                """
                INSERT OR REPLACE INTO clients(client_id, tenant_id, display_name, created_at)
                VALUES (?, ?, ?, ?)
                """,
                (client_id, tenant_id, display_name, _utc_timestamp()),
            )

    def save_engagement(self, engagement: Engagement) -> None:
        self.initialize()
        with self.connect() as connection:
            self._upsert_engagement(connection, engagement)

    def get_engagement(self, engagement_id: str) -> dict[str, Any] | None:
        self.initialize()
        row = self.connect().execute(
            """
            SELECT engagement_id, tenant_id, client_id, scope_json, rules_json, expires_at, updated_at
            FROM engagements WHERE engagement_id = ?
            """,
            (engagement_id,),
        ).fetchone()
        if not row:
            return None
        result = self._row_to_dict(row)
        result["scope"] = result.pop("scope", [])
        result["rules"] = result.pop("rules", {})
        return result

    def engagement_to_model(self, row: dict[str, Any]) -> Engagement:
        rules = row.get("rules", {})
        expires_at = datetime.fromisoformat(row["expires_at"])
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)
        return Engagement(
            engagement_id=row["engagement_id"],
            tenant_id=row["tenant_id"],
            client_id=row["client_id"],
            authorized_targets=tuple(ScopeTarget(pattern=item) for item in row.get("scope", [])),
            rules=RulesOfEngagement(
                allow_network_transport=bool(rules.get("allow_network_transport", False)),
                max_runtime_seconds=int(rules.get("max_runtime_seconds", 30)),
                notes=str(rules.get("notes", "")),
            ),
            expires_at=expires_at,
        )

    def delete_engagement(self, engagement_id: str) -> int:
        self.initialize()
        connection = self.connect()
        with connection:
            connection.execute(
                "DELETE FROM evidence_records WHERE job_id IN (SELECT job_id FROM jobs WHERE engagement_id = ?)",
                (engagement_id,),
            )
            connection.execute("DELETE FROM jobs WHERE engagement_id = ?", (engagement_id,))
            connection.execute("DELETE FROM approvals WHERE engagement_id = ?", (engagement_id,))
            connection.execute("DELETE FROM audit_events WHERE engagement_id = ?", (engagement_id,))
            cursor = connection.execute("DELETE FROM engagements WHERE engagement_id = ?", (engagement_id,))
            return cursor.rowcount

    def export_audit_events_csv(self, limit: int = 500) -> str:
        events = self.list_audit_events(limit=limit)
        lines = ["event_id,tenant_id,engagement_id,action,reason_code,created_at,details"]
        for event in events:
            details = json.dumps(event.get("details", {}), sort_keys=True)
            row = [
                event["event_id"],
                event["tenant_id"],
                event["engagement_id"],
                event["action"],
                event["reason_code"],
                event["created_at"],
                details,
            ]
            lines.append(",".join(f'"{str(value).replace(chr(34), chr(34) * 2)}"' for value in row))
        return "\n".join(lines) + "\n"

    def export_evidence_json(self, limit: int = 500) -> str:
        records = self.list_evidence(limit=limit)
        return json.dumps(records, indent=2, sort_keys=True) + "\n"

    def ensure_usage_schema(self) -> None:
        self.initialize()

    def insert_usage_event(self, event: dict[str, Any]) -> None:
        self.initialize()
        connection = self.connect()
        with connection:
            connection.execute(
                """
                INSERT OR REPLACE INTO usage_events(
                    event_id, tenant_id, client_id, engagement_id, event_type,
                    quantity, unit, metadata_json, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    event["event_id"],
                    event["tenant_id"],
                    event["client_id"],
                    event["engagement_id"],
                    event["event_type"],
                    float(event["quantity"]),
                    event["unit"],
                    _json(event.get("metadata", {})),
                    event["created_at"],
                ),
            )

    def list_usage_events(
        self,
        *,
        engagement_id: str | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        self.initialize()
        query = """
            SELECT event_id, tenant_id, client_id, engagement_id, event_type,
                   quantity, unit, metadata_json, created_at
            FROM usage_events
        """
        params: list[Any] = []
        if engagement_id:
            query += " WHERE engagement_id = ?"
            params.append(engagement_id)
        query += " ORDER BY created_at DESC LIMIT ?"
        params.append(limit)
        cursor = self.connect().execute(query, params)
        rows = []
        for row in cursor.fetchall():
            item = dict(row)
            if item.get("metadata_json"):
                item["metadata"] = json.loads(item.pop("metadata_json"))
            rows.append(item)
        return rows

    def close(self) -> None:
        if self._connection is not None:
            self._connection.close()
            self._connection = None

    def _upsert_engagement(self, connection: sqlite3.Connection, engagement: Engagement) -> None:
        connection.execute(
            """
            INSERT OR IGNORE INTO tenants(tenant_id, display_name, created_at)
            VALUES (?, ?, ?)
            """,
            (engagement.tenant_id, engagement.tenant_id, _utc_timestamp()),
        )
        connection.execute(
            """
            INSERT OR IGNORE INTO clients(client_id, tenant_id, display_name, created_at)
            VALUES (?, ?, ?, ?)
            """,
            (engagement.client_id, engagement.tenant_id, engagement.client_id, _utc_timestamp()),
        )
        connection.execute(
            """
            INSERT OR REPLACE INTO engagements(
                engagement_id, tenant_id, client_id, scope_json, rules_json, expires_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                engagement.engagement_id,
                engagement.tenant_id,
                engagement.client_id,
                _json([scope.pattern for scope in engagement.authorized_targets]),
                _json(
                    {
                        "allow_network_transport": engagement.rules.allow_network_transport,
                        "max_runtime_seconds": engagement.rules.max_runtime_seconds,
                        "notes": engagement.rules.notes,
                    }
                ),
                engagement.expires_at.isoformat(),
                _utc_timestamp(),
            ),
        )

    def _insert_approval(self, connection: sqlite3.Connection, approval: ApprovalRequest) -> None:
        connection.execute(
            """
            INSERT OR REPLACE INTO approvals(
                approval_id, tenant_id, client_id, engagement_id, adapter_id, target,
                requested_by, requested_at, expires_at, state, decided_by, decided_at, decision_reason
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                approval.approval_id,
                approval.tenant_id,
                approval.client_id,
                approval.engagement_id,
                approval.adapter_id,
                approval.target,
                approval.requested_by,
                approval.requested_at.isoformat(),
                approval.expires_at.isoformat(),
                approval.state,
                approval.decided_by,
                approval.decided_at.isoformat() if approval.decided_at else None,
                approval.decision_reason,
            ),
        )

    def _insert_evidence(self, connection: sqlite3.Connection, evidence_records: Iterable[EvidenceRecord]) -> None:
        for evidence in evidence_records:
            connection.execute(
                """
                INSERT OR REPLACE INTO evidence_records(
                    job_id, evidence_id, adapter_id, target, parser_id, tool_version, sha256, content_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    evidence.job_id,
                    evidence.evidence_id,
                    evidence.adapter_id,
                    evidence.target,
                    evidence.parser_id,
                    evidence.tool_version,
                    evidence.sha256,
                    _json(evidence.content),
                ),
            )

    def _insert_audit_event(
        self,
        connection: sqlite3.Connection,
        engagement: Engagement,
        action: str,
        reason_code: str,
        details: dict[str, Any],
    ) -> None:
        connection.execute(
            """
            INSERT INTO audit_events(
                event_id, tenant_id, engagement_id, action, reason_code, created_at, details_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                f"audit-{uuid.uuid4()}",
                engagement.tenant_id,
                engagement.engagement_id,
                action,
                reason_code,
                _utc_timestamp(),
                _json(details),
            ),
        )

    def _current_schema_version(self, connection: sqlite3.Connection) -> int:
        row = connection.execute("SELECT MAX(version) AS version FROM schema_migrations").fetchone()
        return int(row["version"] or 0)

    def _count(self, connection: sqlite3.Connection, table: str) -> int:
        row = connection.execute(f"SELECT COUNT(*) AS count FROM {table}").fetchone()
        return int(row["count"])

    def _row_to_dict(self, row: sqlite3.Row) -> dict[str, Any]:
        result = dict(row)
        for key in ("details_json", "content_json", "scope_json", "rules_json"):
            if key in result and result[key]:
                result[key.removesuffix("_json")] = json.loads(result.pop(key))
        return result


_MIGRATION_001 = """
CREATE TABLE tenants (
    tenant_id TEXT PRIMARY KEY,
    display_name TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE TABLE clients (
    client_id TEXT PRIMARY KEY,
    tenant_id TEXT NOT NULL REFERENCES tenants(tenant_id),
    display_name TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE TABLE engagements (
    engagement_id TEXT PRIMARY KEY,
    tenant_id TEXT NOT NULL REFERENCES tenants(tenant_id),
    client_id TEXT NOT NULL REFERENCES clients(client_id),
    scope_json TEXT NOT NULL,
    rules_json TEXT NOT NULL,
    expires_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE jobs (
    job_id TEXT PRIMARY KEY,
    tenant_id TEXT NOT NULL REFERENCES tenants(tenant_id),
    client_id TEXT NOT NULL REFERENCES clients(client_id),
    engagement_id TEXT NOT NULL REFERENCES engagements(engagement_id),
    adapter_id TEXT NOT NULL,
    target TEXT NOT NULL,
    arguments_json TEXT NOT NULL,
    issued_at TEXT NOT NULL,
    expires_at TEXT NOT NULL,
    signature TEXT NOT NULL,
    status TEXT NOT NULL,
    decision_reason TEXT NOT NULL,
    decision_message TEXT NOT NULL
);

CREATE TABLE evidence_records (
    job_id TEXT NOT NULL REFERENCES jobs(job_id),
    evidence_id TEXT NOT NULL,
    adapter_id TEXT NOT NULL,
    target TEXT NOT NULL,
    parser_id TEXT NOT NULL,
    tool_version TEXT NOT NULL,
    sha256 TEXT NOT NULL,
    content_json TEXT NOT NULL,
    PRIMARY KEY (job_id, evidence_id)
);

CREATE TABLE audit_events (
    event_id TEXT PRIMARY KEY,
    tenant_id TEXT NOT NULL REFERENCES tenants(tenant_id),
    engagement_id TEXT NOT NULL REFERENCES engagements(engagement_id),
    action TEXT NOT NULL,
    reason_code TEXT NOT NULL,
    created_at TEXT NOT NULL,
    details_json TEXT NOT NULL
);

CREATE TABLE report_drafts (
    report_id TEXT PRIMARY KEY,
    engagement_id TEXT NOT NULL REFERENCES engagements(engagement_id),
    evidence_ids_json TEXT NOT NULL,
    finding_ids_json TEXT NOT NULL,
    status TEXT NOT NULL,
    created_at TEXT NOT NULL
);
"""

_MIGRATION_003 = """
CREATE TABLE IF NOT EXISTS usage_events (
    event_id TEXT PRIMARY KEY,
    tenant_id TEXT NOT NULL,
    client_id TEXT NOT NULL,
    engagement_id TEXT NOT NULL,
    event_type TEXT NOT NULL,
    quantity REAL NOT NULL,
    unit TEXT NOT NULL,
    metadata_json TEXT NOT NULL,
    created_at TEXT NOT NULL
);
"""

_MIGRATION_002 = """
ALTER TABLE jobs ADD COLUMN approval_id TEXT;

CREATE TABLE approvals (
    approval_id TEXT PRIMARY KEY,
    tenant_id TEXT NOT NULL REFERENCES tenants(tenant_id),
    client_id TEXT NOT NULL REFERENCES clients(client_id),
    engagement_id TEXT NOT NULL REFERENCES engagements(engagement_id),
    adapter_id TEXT NOT NULL,
    target TEXT NOT NULL,
    requested_by TEXT NOT NULL,
    requested_at TEXT NOT NULL,
    expires_at TEXT NOT NULL,
    state TEXT NOT NULL,
    decided_by TEXT,
    decided_at TEXT,
    decision_reason TEXT NOT NULL
);
"""
