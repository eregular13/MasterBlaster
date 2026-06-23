from __future__ import annotations

from dataclasses import asdict, dataclass, field, replace
from datetime import datetime, timezone
from typing import Any, Mapping


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


@dataclass(frozen=True)
class ScopeTarget:
    pattern: str


@dataclass(frozen=True)
class Tenant:
    tenant_id: str
    display_name: str


@dataclass(frozen=True)
class Client:
    client_id: str
    tenant_id: str
    display_name: str


@dataclass(frozen=True)
class RulesOfEngagement:
    allow_network_transport: bool = False
    max_runtime_seconds: int = 30
    notes: str = "P0 simulator only; no live target access."


@dataclass(frozen=True)
class Engagement:
    engagement_id: str
    tenant_id: str
    client_id: str
    authorized_targets: tuple[ScopeTarget, ...]
    rules: RulesOfEngagement
    expires_at: datetime


@dataclass(frozen=True)
class AdapterManifest:
    adapter_id: str
    name: str
    version: str
    tier: str
    execution_mode: str
    parameters: tuple[str, ...]
    allowed_target_types: tuple[str, ...]
    network_access: bool
    fixture_only: bool
    reviewed: bool
    description: str

    def to_mcp_definition(self) -> dict[str, Any]:
        return {
            "id": self.adapter_id,
            "adapter_id": self.adapter_id,
            "name": self.name,
            "version": self.version,
            "tier": self.tier,
            "execution_mode": self.execution_mode,
            "params": list(self.parameters),
            "description": self.description,
        }


@dataclass(frozen=True)
class PolicyDecision:
    allowed: bool
    reason_code: str
    message: str
    normalized_target: str | None = None


@dataclass(frozen=True)
class JobEnvelope:
    job_id: str
    tenant_id: str
    client_id: str
    engagement_id: str
    adapter_id: str
    target: str
    arguments: Mapping[str, str] = field(default_factory=dict)
    issued_at: datetime = field(default_factory=utc_now)
    expires_at: datetime = field(default_factory=utc_now)
    signature: str = ""

    def unsigned(self) -> "JobEnvelope":
        return replace(self, signature="")

    def to_dict(self, include_signature: bool = True) -> dict[str, Any]:
        data = asdict(self if include_signature else self.unsigned())
        data["issued_at"] = self.issued_at.isoformat()
        data["expires_at"] = self.expires_at.isoformat()
        return data


@dataclass(frozen=True)
class EvidenceRecord:
    evidence_id: str
    job_id: str
    adapter_id: str
    target: str
    parser_id: str
    tool_version: str
    sha256: str
    content: Mapping[str, Any]


@dataclass(frozen=True)
class Finding:
    finding_id: str
    evidence_id: str
    title: str
    severity: str
    confidence: str
    mapping: Mapping[str, str]


@dataclass(frozen=True)
class AuditEvent:
    event_id: str
    tenant_id: str
    engagement_id: str
    action: str
    reason_code: str
    created_at: datetime


@dataclass(frozen=True)
class ReportDraft:
    report_id: str
    engagement_id: str
    evidence_ids: tuple[str, ...]
    finding_ids: tuple[str, ...]
    status: str = "draft"
