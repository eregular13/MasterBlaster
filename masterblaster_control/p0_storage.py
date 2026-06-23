from __future__ import annotations

import json
import sqlite3
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

from .p0_models import Engagement, EvidenceRecord
from .p0_policy import canonical_json
from .runner_simulator import RunnerResult

SCHEMA_VERSION = 1


@dataclass(frozen=True)
class StorageSnapshot:
    tenants: int
    clients: int
    engagements: int
    jobs: int
    evidence_records: int
    audit_events: int


def _utc_timestamp() -> str:
    return datetime.now(timezone.utc).isoformat()


def _json(data: Any) -> str:
    return canonical_json(data)


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
        if self._current_schema_version(connection) != SCHEMA_VERSION:
            raise RuntimeError("P0 storage schema version mismatch")
        connection.commit()

    def record_runner_result(self, result: RunnerResult) -> None:
        self.initialize()
        engagement = result.engagement
        connection = self.connect()
        with connection:
            self._upsert_engagement(connection, engagement)
            if result.job:
                connection.execute(
                    """
                    INSERT OR REPLACE INTO jobs (
                        job_id, tenant_id, client_id, engagement_id, adapter_id,
                        target, arguments_json, issued_at, expires_at, signature,
                        status, decision_reason, decision_message
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
                    "adapter_id": result.job.adapter_id if result.job else None,
                    "target": result.job.target if result.job else result.decision.normalized_target,
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
            jobs=self._count(connection, "jobs"),
            evidence_records=self._count(connection, "evidence_records"),
            audit_events=self._count(connection, "audit_events"),
        )

    def list_audit_events(self, limit: int = 25) -> list[dict[str, Any]]:
        self.initialize()
        cursor = self.connect().execute(
            """
            SELECT event_id, tenant_id, engagement_id, action, reason_code, created_at, details_json
            FROM audit_events
            ORDER BY created_at DESC
            LIMIT ?
            """,
            (limit,),
        )
        return [self._row_to_dict(row) for row in cursor.fetchall()]

    def list_evidence(self, limit: int = 25) -> list[dict[str, Any]]:
        self.initialize()
        cursor = self.connect().execute(
            """
            SELECT evidence_id, job_id, adapter_id, target, parser_id, tool_version, sha256, content_json
            FROM evidence_records
            ORDER BY rowid DESC
            LIMIT ?
            """,
            (limit,),
        )
        return [self._row_to_dict(row) for row in cursor.fetchall()]

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
        for key in ("details_json", "content_json"):
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
