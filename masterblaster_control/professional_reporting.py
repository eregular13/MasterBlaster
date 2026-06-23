"""Client-facing assessment reports with executive summary, findings, and compliance sections."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from .business_config import FirmConfig, load_firm_config
from .engagement_templates import get_template
from .p0_models import EvidenceRecord, Finding
from .p0_storage import P0Storage
from .p3_reporting import project_findings_from_evidence

SEVERITY_ORDER = ("critical", "high", "medium", "low", "info")


@dataclass(frozen=True)
class ProfessionalReport:
    report_id: str
    generated_at: str
    firm_name: str
    client_name: str
    project_name: str
    engagement_id: str
    template_id: str | None
    findings: tuple[Finding, ...]
    evidence_ids: tuple[str, ...]
    severity_counts: dict[str, int]

    def to_dict(self) -> dict[str, Any]:
        return {
            "report_id": self.report_id,
            "generated_at": self.generated_at,
            "firm_name": self.firm_name,
            "client_name": self.client_name,
            "project_name": self.project_name,
            "engagement_id": self.engagement_id,
            "template_id": self.template_id,
            "severity_counts": self.severity_counts,
            "findings": [
                {
                    "finding_id": f.finding_id,
                    "title": f.title,
                    "severity": f.severity,
                    "confidence": f.confidence,
                    "evidence_id": f.evidence_id,
                    "mapping": dict(f.mapping),
                }
                for f in self.findings
            ],
            "evidence_ids": list(self.evidence_ids),
        }


def _severity_counts(findings: tuple[Finding, ...]) -> dict[str, int]:
    counts = {level: 0 for level in SEVERITY_ORDER}
    for finding in findings:
        key = finding.severity.lower()
        counts[key] = counts.get(key, 0) + 1
    return counts


def _remediation_for_finding(finding: Finding) -> str:
    severity = finding.severity.lower()
    obs = finding.mapping.get("observation_id", "")
    if severity == "critical":
        return "Remediate immediately. Validate fix and schedule emergency change control if production is affected."
    if severity == "high":
        return "Prioritize remediation within 30 days. Implement compensating controls until patch is deployed."
    if severity == "medium":
        return "Address in next maintenance window. Document accepted risk if business constraints apply."
    if "tls" in obs or "certificate" in finding.title.lower():
        return "Renew or replace certificates; enforce TLS 1.2+ and disable weak cipher suites."
    if "dns" in obs:
        return "Harden DNS posture (SPF/DMARC/DKIM/DNSSEC) per organizational email security policy."
    if "port" in obs:
        return "Close unnecessary exposed services; restrict management interfaces to trusted networks."
    if "http" in obs:
        return "Implement missing security headers per OWASP Secure Headers guidance."
    return "Review observation in context of asset criticality; track in vulnerability management program."


def _compliance_mapping(finding: Finding) -> list[str]:
    title = finding.title.lower()
    mappings: list[str] = []
    if "tls" in title or "certificate" in title:
        mappings.extend(["SOC 2 CC6.7", "ISO 27001 A.10.1", "PCI-DSS 4.1"])
    if "dns" in title or "dmarc" in title:
        mappings.extend(["SOC 2 CC6.1", "ISO 27001 A.13.2"])
    if "port" in title or "ssh" in title:
        mappings.extend(["SOC 2 CC6.6", "ISO 27001 A.13.1", "PCI-DSS 1.2"])
    if "http" in title:
        mappings.extend(["SOC 2 CC6.1", "ISO 27001 A.14.2", "OWASP ASVS"])
    if not mappings:
        mappings.append("Map to organizational control framework during QA review")
    return mappings


def generate_professional_report(
    storage: P0Storage,
    *,
    engagement_id: str = "engagement-local-simulator",
    client_name: str = "Client",
    project_name: str = "Security Assessment",
    template_id: str | None = None,
    firm_config: FirmConfig | None = None,
    limit: int = 200,
) -> ProfessionalReport:
    config = firm_config or load_firm_config()
    records = storage.list_evidence(limit=limit)
    evidence_records = tuple(
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
    )
    findings = project_findings_from_evidence(evidence_records)
    now = datetime.now(timezone.utc).isoformat()
    return ProfessionalReport(
        report_id=f"RPT-{now.replace(':', '').replace('-', '')[:15]}",
        generated_at=now,
        firm_name=config.firm_name,
        client_name=client_name,
        project_name=project_name,
        engagement_id=engagement_id,
        template_id=template_id,
        findings=findings,
        evidence_ids=tuple(r.evidence_id for r in evidence_records),
        severity_counts=_severity_counts(findings),
    )


def professional_report_markdown(report: ProfessionalReport, *, config: FirmConfig | None = None) -> str:
    cfg = config or load_firm_config()
    template = get_template(report.template_id) if report.template_id else None
    total = sum(report.severity_counts.values())
    critical_high = report.severity_counts.get("critical", 0) + report.severity_counts.get("high", 0)

    lines = [
        f"# Security Assessment Report",
        "",
        f"**{cfg.report_watermark}**",
        "",
        f"| Field | Value |",
        f"| --- | --- |",
        f"| **Prepared by** | {report.firm_name} |",
        f"| **Client** | {report.client_name} |",
        f"| **Project** | {report.project_name} |",
        f"| **Engagement ID** | `{report.engagement_id}` |",
        f"| **Report ID** | `{report.report_id}` |",
        f"| **Generated** | {report.generated_at} |",
    ]
    if template:
        lines.append(f"| **Assessment type** | {template.name} |")
    lines.extend(["", "---", "", "## Executive Summary", ""])
    if total == 0:
        lines.append(
            "Assessment activities were executed under authorized scope. No material findings were "
            "projected from collected evidence in this reporting period. Continue monitoring and "
            "schedule re-assessment per contract terms."
        )
    else:
        lines.append(
            f"This assessment identified **{total}** observations across in-scope assets. "
            f"**{critical_high}** require priority attention (Critical/High). "
            "Detailed findings, evidence references, and remediation guidance are provided below. "
            "This report is intended to support risk prioritization and follow-on remediation services."
        )
    lines.extend(["", "## Findings Summary", "", "| Severity | Count |", "| --- | ---: |"])
    for level in SEVERITY_ORDER:
        count = report.severity_counts.get(level, 0)
        if count:
            lines.append(f"| {level.capitalize()} | {count} |")
    lines.extend(["", "## Scope and Methodology", ""])
    if template:
        lines.append(template.scope_guidance)
        lines.append("")
        lines.append(f"**Workflow:** {len(template.mcp_chain)}-step automated pipeline via MasterBlaster MCP orchestration.")
        lines.append(f"**Recommended tools:** {', '.join(template.recommended_tools)}")
    else:
        lines.append("Assessment conducted per signed rules of engagement using governed MCP orchestration.")
    lines.extend(["", "## Detailed Findings", ""])
    if not report.findings:
        lines.append("_No findings to display._")
    else:
        for index, finding in enumerate(
            sorted(report.findings, key=lambda f: SEVERITY_ORDER.index(f.severity.lower()) if f.severity.lower() in SEVERITY_ORDER else 99),
            start=1,
        ):
            remediation = _remediation_for_finding(finding)
            compliance = ", ".join(_compliance_mapping(finding))
            lines.extend([
                f"### {index}. [{finding.severity.upper()}] {finding.title}",
                "",
                f"- **Finding ID:** `{finding.finding_id}`",
                f"- **Evidence:** `{finding.evidence_id}`",
                f"- **Confidence:** {finding.confidence}",
                f"- **Compliance mapping:** {compliance}",
                f"- **Remediation:** {remediation}",
                "",
            ])
    lines.extend([
        "## Compliance Appendix",
        "",
        "Findings may be mapped to common control frameworks during client QA:",
        "",
        "- **SOC 2** — Trust Services Criteria (Security, Availability, Confidentiality)",
        "- **ISO/IEC 27001** — Annex A technical and organizational controls",
        "- **PCI-DSS** — Network segmentation, encryption, and access control requirements",
        "",
        "## Evidence Index",
        "",
        "| Evidence ID | Adapter |",
        "| --- | --- |",
    ])
    for eid in report.evidence_ids[:50]:
        lines.append(f"| `{eid}` | — |")
    if len(report.evidence_ids) > 50:
        lines.append(f"| _+{len(report.evidence_ids) - 50} more_ | — |")
    lines.extend([
        "",
        "---",
        "",
        f"_{cfg.firm_name} — {cfg.tagline}_",
    ])
    return "\n".join(lines)


def export_findings_csv(report: ProfessionalReport) -> str:
    lines = ["finding_id,severity,title,evidence_id,confidence,remediation"]
    for finding in report.findings:
        remediation = _remediation_for_finding(finding).replace('"', '""')
        title = finding.title.replace('"', '""')
        lines.append(
            f'"{finding.finding_id}","{finding.severity}","{title}","{finding.evidence_id}",'
            f'"{finding.confidence}","{remediation}"'
        )
    return "\n".join(lines) + "\n"


def export_report_json(report: ProfessionalReport) -> str:
    return json.dumps(report.to_dict(), indent=2, sort_keys=True) + "\n"