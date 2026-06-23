"""Warlord assault-chain orchestrator — cracks the whip across multiple MCPs."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from .mcp_tool_arsenal import (
    DEFAULT_ASSAULT_CHAIN,
    FULL_REGISTRY_QUEUE,
    WARLORD_TAGLINE,
    tools_for_mcp,
)
from .p0_approvals import approve_request, request_approval
from .p0_models import Engagement
from .p0_policy import parse_target
from .runner_simulator import MANIFESTS, RunnerSimulator


def _resolve_target_for_mcp(manifest, raw_target: str) -> str:
    """Pick a target form the MCP accepts (e.g. promote domain → URL for web MCPs)."""
    candidates = [raw_target]
    if "url" in manifest.allowed_target_types and not raw_target.startswith(("http://", "https://")):
        candidates.extend([f"https://{raw_target}/", f"http://{raw_target}/"])
    for candidate in candidates:
        try:
            target_type, normalized, _ = parse_target(candidate)
        except Exception:
            continue
        if target_type in manifest.allowed_target_types:
            return normalized
    return raw_target


@dataclass(frozen=True)
class WarlordStepResult:
    step_index: int
    adapter_id: str
    mcp_name: str
    tools: tuple[str, ...]
    status: str
    reason_code: str
    evidence_id: str | None

    def to_dict(self) -> dict[str, Any]:
        return {
            "step": self.step_index,
            "adapter_id": self.adapter_id,
            "mcp_name": self.mcp_name,
            "tools": list(self.tools),
            "status": self.status,
            "reason_code": self.reason_code,
            "evidence_id": self.evidence_id,
        }


@dataclass(frozen=True)
class WarlordChainResult:
    target: str
    engagement_id: str
    chain: tuple[str, ...]
    steps: tuple[WarlordStepResult, ...]
    completed: int
    denied: int

    @property
    def success_rate(self) -> float:
        if not self.steps:
            return 0.0
        return self.completed / len(self.steps)


def execute_warlord_step(
    runner: RunnerSimulator,
    engagement: Engagement,
    target: str,
    adapter_id: str,
    step_index: int,
    *,
    now: datetime | None = None,
):
    """Run a single MCP strike with auto-approval and evidence capture."""
    current = now or datetime.now(timezone.utc)
    if current.tzinfo is None:
        current = current.replace(tzinfo=timezone.utc)

    manifest = MANIFESTS.get(adapter_id)
    tools = tools_for_mcp(adapter_id)
    if manifest is None:
        step = WarlordStepResult(
            step_index, adapter_id, adapter_id, tools, "denied", "UNKNOWN_MCP", None
        )
        return step, None

    strike_target = _resolve_target_for_mcp(manifest, target)
    approval = approve_request(
        request_approval(engagement, adapter_id, strike_target, now=current),
        now=current,
    )
    result = runner.run(
        adapter_id,
        strike_target,
        engagement=engagement,
        approval=approval,
        now=current,
    )
    evidence_id = result.evidence[0].evidence_id if result.evidence else None
    step = WarlordStepResult(
        step_index=step_index,
        adapter_id=adapter_id,
        mcp_name=manifest.name,
        tools=tools,
        status=result.status,
        reason_code=result.decision.reason_code,
        evidence_id=evidence_id,
    )
    return step, result


def _summarize_steps(steps: list[WarlordStepResult]) -> tuple[int, int]:
    completed = sum(1 for step in steps if step.status == "completed")
    denied = len(steps) - completed
    return completed, denied


def execute_warlord_chain(
    runner: RunnerSimulator,
    engagement: Engagement,
    target: str,
    *,
    chain: tuple[str, ...] | None = None,
    now: datetime | None = None,
) -> WarlordChainResult:
    """Execute a multi-MCP assault chain with per-step approval and evidence capture."""
    selected = chain or DEFAULT_ASSAULT_CHAIN
    steps: list[WarlordStepResult] = []
    for index, adapter_id in enumerate(selected, start=1):
        step, _ = execute_warlord_step(
            runner, engagement, target, adapter_id, index, now=now
        )
        steps.append(step)
    completed, denied = _summarize_steps(steps)
    return WarlordChainResult(
        target=target,
        engagement_id=engagement.engagement_id,
        chain=selected,
        steps=tuple(steps),
        completed=completed,
        denied=denied,
    )


def execute_registry_queue(
    runner: RunnerSimulator,
    engagement: Engagement,
    target: str,
    *,
    now: datetime | None = None,
) -> WarlordChainResult:
    """Deploy all 22 MCPs in catalog order — the full parallel registry queue."""
    return execute_warlord_chain(
        runner, engagement, target, chain=FULL_REGISTRY_QUEUE, now=now
    )


def warlord_chain_markdown(
    result: WarlordChainResult,
    *,
    title: str = "Warlord Assault Chain Report",
    section: str = "Chain Execution",
) -> str:
    lines = [
        f"# {title}",
        "",
        f"> {WARLORD_TAGLINE}",
        "",
        f"**Target:** `{result.target}`",
        f"**Engagement:** `{result.engagement_id}`",
        f"**MCPs deployed:** {len(result.steps)}",
        f"**Completed:** {result.completed} | **Denied:** {result.denied}",
        "",
        f"## {section}",
        "",
        "| Step | MCP | Tools | Status | Evidence |",
        "| ---: | --- | --- | --- | --- |",
    ]
    for step in result.steps:
        tools = ", ".join(step.tools) or "—"
        evidence = step.evidence_id or "—"
        lines.append(
            f"| {step.step_index} | `{step.adapter_id}` | {tools} | "
            f"**{step.status}** | `{evidence}` |"
        )
    return "\n".join(lines)


def registry_queue_markdown(result: WarlordChainResult) -> str:
    return warlord_chain_markdown(
        result,
        title="Warlord Registry Queue Report — 22 MCPs Under the Whip",
        section="Registry Queue Execution",
    )


def warlord_chain_json(
    result: WarlordChainResult,
    *,
    queue_type: str = "chain",
) -> str:
    import json

    return json.dumps(
        {
            "tagline": WARLORD_TAGLINE,
            "queue_type": queue_type,
            "target": result.target,
            "engagement_id": result.engagement_id,
            "chain": list(result.chain),
            "completed": result.completed,
            "denied": result.denied,
            "success_rate": result.success_rate,
            "steps": [step.to_dict() for step in result.steps],
        },
        indent=2,
        sort_keys=True,
    )