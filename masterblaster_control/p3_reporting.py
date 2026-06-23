from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Any, Iterable

from .p0_models import EvidenceRecord, Finding
from .p0_storage import P0Storage

DISCLAIMER = (
    "SIMULATOR DRAFT ONLY — not a compliance certification, penetration test report, "
    "or attestation of security posture."
)


@dataclass(frozen=True)
class ComplianceDraft:
    report_id: str
    generated_at: str
    engagement_id: str
    findings: tuple[Finding, ...]
    evidence_ids: tuple[str, ...]
    disclaimer: str = DISCLAIMER

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["findings"] = [asdict(finding) for finding in self.findings]
        return data


def project_findings_from_evidence(evidence_records: Iterable[EvidenceRecord]) -> tuple[Finding, ...]:
    findings: list[Finding] = []
    for evidence in evidence_records:
        observations = evidence.content.get("observations", [])
        for observation in observations:
            obs_id = str(observation.get("id", "unknown"))
            value = observation.get("value")
            severity, title = _classify_observation(obs_id, value)
            findings.append(
                Finding(
                    finding_id=f"finding-{evidence.evidence_id}-{obs_id}",
                    evidence_id=evidence.evidence_id,
                    title=title,
                    severity=severity,
                    confidence="simulator-fixture",
                    mapping={"observation_id": obs_id, "adapter_id": evidence.adapter_id},
                )
            )
    return tuple(findings)


def generate_compliance_draft(
    storage: P0Storage,
    engagement_id: str = "engagement-local-simulator",
    limit: int = 100,
) -> ComplianceDraft:
    records = storage.list_evidence(limit=limit)
    evidence_records = [
        EvidenceRecord(
            evidence_id=row["evidence_id"],
            job_id=row["job_id"],
            adapter_id=row["adapter_id"],
            target=row["target"],
            parser_id=row["parser_id"],
            tool_version=row["tool_version"],
            sha256=row["sha256"],
            content=row.get("content", {}),
        )
        for row in records
    ]
    findings = project_findings_from_evidence(evidence_records)
    now = datetime.now(timezone.utc).isoformat()
    return ComplianceDraft(
        report_id=f"report-{now.replace(':', '').replace('-', '')[:15]}",
        generated_at=now,
        engagement_id=engagement_id,
        findings=findings,
        evidence_ids=tuple(record.evidence_id for record in evidence_records),
    )


def compliance_draft_markdown(draft: ComplianceDraft) -> str:
    lines = [
        "# MasterBlaster Compliance Draft",
        "",
        f"**Generated:** {draft.generated_at}",
        f"**Engagement:** {draft.engagement_id}",
        "",
        f"> {draft.disclaimer}",
        "",
        "## Findings",
        "",
    ]
    if not draft.findings:
        lines.append("_No findings projected from simulator evidence._")
    else:
        lines.append("| Severity | Title | Evidence | Observation |")
        lines.append("| --- | --- | --- | --- |")
        for finding in draft.findings:
            lines.append(
                f"| {finding.severity} | {finding.title} | {finding.evidence_id} | "
                f"{finding.mapping.get('observation_id', '')} |"
            )
    lines.extend(["", "## Evidence IDs", "", ", ".join(draft.evidence_ids) or "_none_"])
    return "\n".join(lines)


def export_compliance_draft_json(draft: ComplianceDraft) -> str:
    return json.dumps(draft.to_dict(), indent=2, sort_keys=True) + "\n"


def _classify_observation(obs_id: str, value: Any) -> tuple[str, str]:
    if obs_id.endswith("expired") and value is True:
        return "high", "Certificate expired in fixture scenario"
    if obs_id == "tls.weak_protocols" and value:
        return "medium", "Weak TLS protocols observed in fixture"
    if obs_id == "port.open" and isinstance(value, list) and 22 in value:
        return "low", "SSH port open in fixture scan"
    if obs_id.startswith("http.") and not value:
        return "medium", f"Missing HTTP control: {obs_id}"
    if obs_id.startswith("dns.") and "reject" in str(value).lower():
        return "info", f"DNS posture control present: {obs_id}"
    return "info", f"Fixture observation: {obs_id}"