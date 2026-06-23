from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Any, Iterable

from .p0_models import Engagement
from .runner_simulator import MANIFESTS

DISCLAIMER = (
    "WORKFLOW DRAFT ONLY — non-executing planning artifact. "
    "Each step still requires human approval and runner validation. "
    "Not a compliance certification or live assessment plan."
)

DEFAULT_OBJECTIVES = (
    "inventory-fixture",
    "dns-posture-fixture",
    "http-headers-fixture",
    "tls-cert-expiry-fixture",
    "mock-port-scan",
    "mock-web-crawl",
)


@dataclass(frozen=True)
class WorkflowStep:
    step_id: str
    adapter_id: str
    name: str
    tier: str
    rationale: str
    requires_approval: bool = True

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class WorkflowDraft:
    draft_id: str
    generated_at: str
    engagement_id: str
    target_scope: tuple[str, ...]
    objectives: tuple[str, ...]
    steps: tuple[WorkflowStep, ...]
    disclaimer: str = DISCLAIMER

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["steps"] = [step.to_dict() for step in self.steps]
        return data


_ADAPTER_OBJECTIVE_MAP = {
    "inventory-fixture": "a0.fixture.inventory",
    "dns-posture-fixture": "a2.dns.posture",
    "http-headers-fixture": "a3.http.headers",
    "tls-cert-expiry-fixture": "a4.tls.cert_expiry",
    "mock-port-scan": "a5.port.scan_sim",
    "mock-web-crawl": "a6.web.crawl_sim",
}


def generate_workflow_draft(
    engagement: Engagement,
    objectives: Iterable[str] | None = None,
) -> WorkflowDraft:
    selected = tuple(objectives or DEFAULT_OBJECTIVES)
    steps: list[WorkflowStep] = []
    for index, objective in enumerate(selected, start=1):
        adapter_id = _ADAPTER_OBJECTIVE_MAP.get(objective)
        if not adapter_id:
            continue
        manifest = MANIFESTS.get(adapter_id)
        if not manifest or not manifest.reviewed:
            continue
        steps.append(
            WorkflowStep(
                step_id=f"step-{index:02d}",
                adapter_id=adapter_id,
                name=manifest.name,
                tier=manifest.tier,
                rationale=f"Objective '{objective}' maps to reviewed fixture adapter {adapter_id}.",
            )
        )

    now = datetime.now(timezone.utc).isoformat()
    return WorkflowDraft(
        draft_id=f"workflow-{now.replace(':', '').replace('-', '')[:15]}",
        generated_at=now,
        engagement_id=engagement.engagement_id,
        target_scope=tuple(scope.pattern for scope in engagement.authorized_targets),
        objectives=selected,
        steps=tuple(steps),
    )


def workflow_draft_markdown(draft: WorkflowDraft) -> str:
    lines = [
        "# MasterBlaster Workflow Draft",
        "",
        f"**Generated:** {draft.generated_at}",
        f"**Engagement:** {draft.engagement_id}",
        f"**Scope:** {', '.join(draft.target_scope) or 'N/A'}",
        "",
        f"> {draft.disclaimer}",
        "",
        "## Objectives",
        "",
    ]
    for objective in draft.objectives:
        lines.append(f"- {objective}")
    lines.extend(["", "## Proposed Steps", "", "| Step | Adapter | Tier | Approval | Rationale |", "| --- | --- | --- | --- | --- |"])
    for step in draft.steps:
        lines.append(
            f"| {step.step_id} | {step.adapter_id} | {step.tier} | "
            f"{'required' if step.requires_approval else 'n/a'} | {step.rationale} |"
        )
    if not draft.steps:
        lines.append("| _none_ | — | — | — | No reviewed adapters matched objectives |")
    return "\n".join(lines)


def export_workflow_draft_json(draft: WorkflowDraft) -> str:
    return json.dumps(draft.to_dict(), indent=2, sort_keys=True) + "\n"