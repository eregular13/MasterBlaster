"""Statement of Work generator — converts consulting proposals into client-ready SOW documents."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from .business_config import FirmConfig, load_firm_config
from .findings_proposal import ConsultingProposal, generate_consulting_proposal
from .professional_reporting import ProfessionalReport


@dataclass(frozen=True)
class StatementOfWork:
    sow_id: str
    generated_at: str
    effective_date: str
    client_name: str
    firm_name: str
    engagement_id: str
    proposal_id: str
    total_value_usd: float
    deliverables: tuple[str, ...]
    acceptance_criteria: tuple[str, ...]
    payment_terms: str

    def to_dict(self) -> dict:
        return {
            "sow_id": self.sow_id,
            "generated_at": self.generated_at,
            "effective_date": self.effective_date,
            "client_name": self.client_name,
            "firm_name": self.firm_name,
            "engagement_id": self.engagement_id,
            "proposal_id": self.proposal_id,
            "total_value_usd": self.total_value_usd,
            "deliverables": list(self.deliverables),
            "acceptance_criteria": list(self.acceptance_criteria),
            "payment_terms": self.payment_terms,
        }


def generate_sow_from_proposal(
    proposal: ConsultingProposal,
    report: ProfessionalReport,
    *,
    config: FirmConfig | None = None,
) -> StatementOfWork:
    cfg = config or load_firm_config()
    now = datetime.now(timezone.utc)
    deliverables = tuple(
        f"{item.service_sku}: {item.title} ({item.estimated_hours:g} hours)"
        for item in proposal.line_items
    )
    if not deliverables:
        deliverables = ("Security advisory services per agreed scope",)

    return StatementOfWork(
        sow_id=f"SOW-{now.strftime('%Y%m%d%H%M%S')}",
        generated_at=now.isoformat(),
        effective_date=now.date().isoformat(),
        client_name=proposal.client_name,
        firm_name=proposal.firm_name,
        engagement_id=proposal.engagement_id,
        proposal_id=proposal.proposal_id,
        total_value_usd=proposal.total_value_usd,
        deliverables=deliverables,
        acceptance_criteria=(
            "All Critical/High findings remediated or formally accepted with documented risk",
            "Re-test validation report delivered within 10 business days of remediation completion",
            "Client sign-off on deliverables within 5 business days of submission",
        ),
        payment_terms="50% upon SOW execution; 50% upon deliverable acceptance",
    )


def generate_sow_from_report(
    report: ProfessionalReport,
    *,
    config: FirmConfig | None = None,
) -> tuple[StatementOfWork, ConsultingProposal]:
    proposal = generate_consulting_proposal(report, config=config)
    sow = generate_sow_from_proposal(proposal, report, config=config)
    return sow, proposal


def sow_markdown(sow: StatementOfWork, proposal: ConsultingProposal) -> str:
    lines = [
        "# Statement of Work",
        "",
        f"**SOW ID:** `{sow.sow_id}`",
        f"**Prepared by:** {sow.firm_name}",
        f"**Client:** {sow.client_name}",
        f"**Effective date:** {sow.effective_date}",
        f"**Related proposal:** `{sow.proposal_id}`",
        f"**Related engagement:** `{sow.engagement_id}`",
        "",
        "## 1. Scope of Services",
        "",
        "The following services are authorized under this Statement of Work:",
        "",
    ]
    for index, item in enumerate(proposal.line_items, start=1):
        lines.extend([
            f"### 1.{index} {item.title} (`{item.service_sku}`)",
            "",
            item.description,
            "",
            f"- **Estimated effort:** {item.estimated_hours:g} hours",
            f"- **Estimated value:** ${item.estimated_value_usd:,.0f}",
            "",
        ])
    lines.extend([
        "## 2. Deliverables",
        "",
    ])
    for deliverable in sow.deliverables:
        lines.append(f"- {deliverable}")
    lines.extend([
        "",
        "## 3. Acceptance Criteria",
        "",
    ])
    for criterion in sow.acceptance_criteria:
        lines.append(f"- {criterion}")
    lines.extend([
        "",
        "## 4. Commercial Terms",
        "",
        f"**Total contract value:** ${sow.total_value_usd:,.0f}",
        f"**Payment terms:** {sow.payment_terms}",
        f"**Proposal valid until:** {proposal.valid_until[:10]}",
        "",
        "## 5. Authorization",
        "",
        "| Party | Name | Signature | Date |",
        "| --- | --- | --- | --- |",
        f"| Service Provider | {sow.firm_name} | _________________________ | _________ |",
        f"| Client | {sow.client_name} | _________________________ | _________ |",
        "",
        "---",
        "",
        "_This SOW is subject to the master services agreement and rules of engagement on file._",
    ])
    return "\n".join(lines)