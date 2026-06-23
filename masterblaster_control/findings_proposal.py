"""Findings-to-proposal generator — converts vulnerabilities into consulting upsell opportunities."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from .business_config import FirmConfig, load_firm_config
from .professional_reporting import ProfessionalReport, _remediation_for_finding


@dataclass(frozen=True)
class ProposalLineItem:
    service_sku: str
    title: str
    description: str
    estimated_hours: float
    estimated_value_usd: float
    related_findings: tuple[str, ...]


@dataclass(frozen=True)
class ConsultingProposal:
    proposal_id: str
    generated_at: str
    valid_until: str
    client_name: str
    engagement_id: str
    firm_name: str
    line_items: tuple[ProposalLineItem, ...]
    total_hours: float
    total_value_usd: float

    def to_dict(self) -> dict:
        return {
            "proposal_id": self.proposal_id,
            "generated_at": self.generated_at,
            "valid_until": self.valid_until,
            "client_name": self.client_name,
            "engagement_id": self.engagement_id,
            "firm_name": self.firm_name,
            "total_hours": self.total_hours,
            "total_value_usd": self.total_value_usd,
            "line_items": [
                {
                    "service_sku": item.service_sku,
                    "title": item.title,
                    "description": item.description,
                    "estimated_hours": item.estimated_hours,
                    "estimated_value_usd": item.estimated_value_usd,
                    "related_findings": list(item.related_findings),
                }
                for item in self.line_items
            ],
        }


def _line_items_from_report(report: ProfessionalReport, hourly_rate: float) -> list[ProposalLineItem]:
    items: list[ProposalLineItem] = []
    critical_high = [f for f in report.findings if f.severity.lower() in {"critical", "high"}]
    medium = [f for f in report.findings if f.severity.lower() == "medium"]

    if critical_high:
        hours = max(16.0, len(critical_high) * 4.0)
        items.append(
            ProposalLineItem(
                service_sku="REM-001",
                title="Emergency Remediation Implementation",
                description="Priority remediation for Critical/High findings including patch deployment, configuration hardening, and validation.",
                estimated_hours=hours,
                estimated_value_usd=hours * hourly_rate,
                related_findings=tuple(f.finding_id for f in critical_high),
            )
        )

    if medium:
        hours = max(8.0, len(medium) * 2.0)
        items.append(
            ProposalLineItem(
                service_sku="REM-002",
                title="Standard Remediation Sprint",
                description="Structured remediation of Medium-severity findings with change management support.",
                estimated_hours=hours,
                estimated_value_usd=hours * hourly_rate,
                related_findings=tuple(f.finding_id for f in medium),
            )
        )

    tls_findings = [f for f in report.findings if "tls" in f.title.lower() or "certificate" in f.title.lower()]
    if tls_findings:
        items.append(
            ProposalLineItem(
                service_sku="CFG-001",
                title="TLS & Certificate Hardening",
                description="Certificate lifecycle review, cipher suite hardening, and automated renewal recommendations.",
                estimated_hours=12.0,
                estimated_value_usd=12.0 * hourly_rate,
                related_findings=tuple(f.finding_id for f in tls_findings),
            )
        )

    if report.findings:
        items.append(
            ProposalLineItem(
                service_sku="MON-001",
                title="Continuous Security Monitoring (12-month)",
                description="Ongoing vulnerability scanning, monthly executive reporting, and quarterly re-assessment.",
                estimated_hours=40.0,
                estimated_value_usd=40.0 * hourly_rate * 0.85,
                related_findings=tuple(f.finding_id for f in report.findings[:5]),
            )
        )
        items.append(
            ProposalLineItem(
                service_sku="COMP-001",
                title="Compliance Readiness Workshop",
                description="SOC 2 / ISO 27001 / PCI gap analysis workshop with control mapping from assessment findings.",
                estimated_hours=16.0,
                estimated_value_usd=16.0 * hourly_rate,
                related_findings=tuple(f.finding_id for f in report.findings[:3]),
            )
        )

    if not items and report.findings:
        items.append(
            ProposalLineItem(
                service_sku="ADV-001",
                title="Security Advisory Retainer",
                description="Post-assessment advisory support for architecture review and security roadmap planning.",
                estimated_hours=20.0,
                estimated_value_usd=20.0 * hourly_rate,
                related_findings=tuple(f.finding_id for f in report.findings),
            )
        )

    return items


def generate_consulting_proposal(
    report: ProfessionalReport,
    *,
    config: FirmConfig | None = None,
) -> ConsultingProposal:
    cfg = config or load_firm_config()
    now = datetime.now(timezone.utc)
    valid = now + timedelta(days=cfg.proposal_valid_days)
    line_items = tuple(_line_items_from_report(report, cfg.default_hourly_rate_usd))
    total_hours = sum(item.estimated_hours for item in line_items)
    total_value = sum(item.estimated_value_usd for item in line_items)
    return ConsultingProposal(
        proposal_id=f"PROP-{now.strftime('%Y%m%d%H%M%S')}",
        generated_at=now.isoformat(),
        valid_until=valid.isoformat(),
        client_name=report.client_name,
        engagement_id=report.engagement_id,
        firm_name=report.firm_name,
        line_items=line_items,
        total_hours=total_hours,
        total_value_usd=total_value,
    )


def proposal_markdown(proposal: ConsultingProposal, report: ProfessionalReport | None = None) -> str:
    lines = [
        "# Consulting Services Proposal",
        "",
        f"**Prepared by:** {proposal.firm_name}",
        f"**Client:** {proposal.client_name}",
        f"**Proposal ID:** `{proposal.proposal_id}`",
        f"**Valid until:** {proposal.valid_until}",
        f"**Related engagement:** `{proposal.engagement_id}`",
        "",
        "## Recommended Services",
        "",
        "| SKU | Service | Hours | Est. Value (USD) |",
        "| --- | --- | ---: | ---: |",
    ]
    for item in proposal.line_items:
        lines.append(
            f"| {item.service_sku} | {item.title} | {item.estimated_hours:g} | ${item.estimated_value_usd:,.0f} |"
        )
    lines.extend([
        "",
        f"**Total estimated investment:** ${proposal.total_value_usd:,.0f} ({proposal.total_hours:g} hours)",
        "",
        "## Service Details",
        "",
    ])
    for item in proposal.line_items:
        lines.extend([
            f"### {item.service_sku} — {item.title}",
            "",
            item.description,
            "",
            f"_Related findings: {len(item.related_findings)}_",
            "",
        ])
    if report and report.findings:
        lines.extend(["## Finding Remediation Summary", ""])
        for finding in report.findings[:10]:
            lines.append(f"- **[{finding.severity.upper()}]** {finding.title}: {_remediation_for_finding(finding)}")
    lines.extend([
        "",
        "---",
        "",
        "_This proposal is based on assessment findings and is subject to scope confirmation._",
    ])
    return "\n".join(lines)