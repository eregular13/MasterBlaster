from __future__ import annotations

from dataclasses import replace

from .p7_workflow_generator import WorkflowDraft, WorkflowStep

ASSISTANT_DISCLAIMER = (
    "ASSISTANT ENRICHMENT — deterministic planning suggestions only. "
    "Does not execute adapters, approve jobs, or override human gates."
)

_SUGGESTIONS = {
    "a0.fixture.inventory": "Confirm asset inventory fixture aligns with engagement scope.",
    "a2.dns.posture": "Review SPF/DMARC/DNSSEC fixture observations for reporting draft.",
    "a3.http.headers": "Map HTTP header fixtures to client hardening recommendations.",
    "a4.tls.cert_expiry": "Check certificate expiry fixture against renewal calendar.",
    "a5.port.scan_sim": "Validate mock port scan output against approved scope only.",
    "a6.web.crawl_sim": "Use crawl fixture to plan manual review — no live HTTP.",
}


def enrich_workflow_draft(draft: WorkflowDraft) -> WorkflowDraft:
    enriched_steps = []
    for step in draft.steps:
        suggestion = _SUGGESTIONS.get(step.adapter_id, "Review simulator fixture output before reporting.")
        enriched_steps.append(
            replace(
                step,
                rationale=f"{step.rationale} Suggested checks: {suggestion}",
            )
        )
    return replace(draft, steps=tuple(enriched_steps))


def assistant_markdown(draft: WorkflowDraft) -> str:
    enriched = enrich_workflow_draft(draft)
    lines = [
        "# Workflow Assistant Enrichment",
        "",
        f"> {ASSISTANT_DISCLAIMER}",
        "",
        f"**Draft:** {enriched.draft_id}",
        f"**Engagement:** {enriched.engagement_id}",
        "",
        "## Enriched Steps",
        "",
    ]
    for step in enriched.steps:
        lines.append(f"- **{step.step_id}** `{step.adapter_id}` — {step.rationale}")
    return "\n".join(lines)