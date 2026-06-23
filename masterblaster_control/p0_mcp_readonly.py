from __future__ import annotations

import uuid
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Callable, Literal, Protocol

from .p0_acceptance import acceptance_dashboard_markdown, acceptance_summary
from .p0_resources import P0Resource, list_resources, read_resource, resource_summary_markdown
from .p0_storage import StorageSnapshot

ToolName = Literal["planning_brief", "report_draft"]


class UnknownReadOnlyToolError(KeyError):
    pass


@dataclass(frozen=True)
class ReadOnlyToolDescriptor:
    name: ToolName
    title: str
    description: str
    output_type: str = "text/markdown"
    non_executing: bool = True

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class ReadOnlyToolResult:
    tool_name: ToolName
    generated_at: str
    content_type: str
    body: str
    non_executing: bool = True

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


class ReadOnlyStorageView(Protocol):
    def snapshot(self) -> StorageSnapshot:
        ...

    def list_audit_events(
        self,
        *,
        tenant_id: str,
        engagement_id: str | None = None,
        limit: int = 25,
    ) -> list[dict[str, object]]:
        ...

    def list_evidence(
        self,
        *,
        tenant_id: str,
        engagement_id: str | None = None,
        limit: int = 25,
    ) -> list[dict[str, object]]:
        ...


class EmptyReadOnlyStorage:
    def snapshot(self) -> StorageSnapshot:
        return StorageSnapshot(0, 0, 0, 0, 0, 0, 0)

    def list_audit_events(
        self,
        *,
        tenant_id: str,
        engagement_id: str | None = None,
        limit: int = 25,
    ) -> list[dict[str, object]]:
        return []

    def list_evidence(
        self,
        *,
        tenant_id: str,
        engagement_id: str | None = None,
        limit: int = 25,
    ) -> list[dict[str, object]]:
        return []


_TOOLS: tuple[ReadOnlyToolDescriptor, ...] = (
    ReadOnlyToolDescriptor(
        name="planning_brief",
        title="Planning Brief",
        description="Renders a non-executing engagement planning brief from registered P0 resources.",
    ),
    ReadOnlyToolDescriptor(
        name="report_draft",
        title="Report Draft",
        description="Renders a simulator-only report draft from stored audit/evidence summaries.",
    ),
)

_TOOL_BY_NAME = {tool.name: tool for tool in _TOOLS}


class P0ReadOnlyMCPFacade:
    """Dependency-free MCP-shaped facade for P0 resources and draft tools.

    This is deliberately not a transport server. It is the safe core a future
    MCP stdio/http wrapper can delegate to without gaining job execution powers.
    """

    def __init__(
        self,
        storage: ReadOnlyStorageView | None = None,
        clock: Callable[[], datetime] | None = None,
    ):
        self._storage = storage or EmptyReadOnlyStorage()
        self._clock = clock or (lambda: datetime.now(timezone.utc))

    def list_resource_descriptors(self) -> tuple[dict[str, object], ...]:
        return tuple(resource.to_dict() for resource in list_resources())

    def read_resource(self, uri: str) -> P0Resource:
        return read_resource(uri)

    def list_tool_descriptors(self) -> tuple[dict[str, object], ...]:
        return tuple(tool.to_dict() for tool in _TOOLS)

    def render_tool(
        self,
        name: ToolName,
        *,
        tenant_id: str | None = None,
        engagement_id: str | None = None,
    ) -> ReadOnlyToolResult:
        if name not in _TOOL_BY_NAME:
            raise UnknownReadOnlyToolError(f"Unknown read-only P0 tool: {name}")
        if name == "planning_brief":
            return self._planning_brief()
        if name == "report_draft":
            return self._report_draft(tenant_id=tenant_id, engagement_id=engagement_id)
        raise UnknownReadOnlyToolError(f"Unknown read-only P0 tool: {name}")

    def _planning_brief(self) -> ReadOnlyToolResult:
        body = "\n\n".join(
            [
                "# MasterBlaster P0 Planning Brief",
                _disclaimer(),
                resource_summary_markdown(),
                "## Acceptance Snapshot",
                acceptance_dashboard_markdown(),
            ]
        )
        return self._result("planning_brief", body)

    def _report_draft(
        self,
        *,
        tenant_id: str | None = None,
        engagement_id: str | None = None,
    ) -> ReadOnlyToolResult:
        snapshot = self._storage.snapshot()
        if tenant_id:
            audit_events = self._storage.list_audit_events(
                tenant_id=tenant_id,
                engagement_id=engagement_id,
                limit=10,
            )
            evidence_records = self._storage.list_evidence(
                tenant_id=tenant_id,
                engagement_id=engagement_id,
                limit=10,
            )
            scope_line = f"Tenant scope: {tenant_id}" + (f" / engagement {engagement_id}" if engagement_id else "")
        else:
            audit_events = []
            evidence_records = []
            scope_line = "Stored audit/evidence summaries require an explicit tenant scope."
        summary = acceptance_summary()
        audit_lines = "\n".join(
            f"- {event['created_at']} {event['action']} {event['reason_code']}"
            for event in audit_events
        ) or "(no audit events)"
        evidence_lines = "\n".join(
            f"- {record['evidence_id']} job={record['job_id']} sha256={record['sha256']}"
            for record in evidence_records
        ) or "(no evidence records)"
        body = f"""# MasterBlaster P0 Report Draft

{_disclaimer()}

## Storage Snapshot

{scope_line}

- Tenants: {snapshot.tenants}
- Clients: {snapshot.clients}
- Engagements: {snapshot.engagements}
- Approvals: {snapshot.approvals}
- Jobs: {snapshot.jobs}
- Evidence records: {snapshot.evidence_records}
- Audit events: {snapshot.audit_events}

## Latest Audit Events

{audit_lines}

## Latest Evidence

{evidence_lines}

## Acceptance Snapshot

- Overall: {summary.overall_percent}%
- P1 gate: {summary.p1_gate_percent}%
- P1 blockers: {', '.join(summary.p1_blockers) or 'none'}
"""
        return self._result("report_draft", body.strip())

    def _result(self, name: ToolName, body: str) -> ReadOnlyToolResult:
        return ReadOnlyToolResult(
            tool_name=name,
            generated_at=self._clock().isoformat(),
            content_type=_TOOL_BY_NAME[name].output_type,
            body=body,
        )


def _disclaimer() -> str:
    return (
        "This artifact is a simulator draft only. It cannot execute jobs, approve scope, "
        "contact targets, or certify compliance."
    )


def demo_session_id() -> str:
    return f"readonly-mcp-demo-{uuid.uuid4()}"
