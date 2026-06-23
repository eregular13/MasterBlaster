from __future__ import annotations

from dataclasses import dataclass

from .p0_models import AdapterManifest, Engagement, PolicyDecision
from .p0_policy import REASON_NETWORK_TRANSPORT, evaluate_policy
from .p9_feature_flags import is_feature_enabled

A7_ADAPTER_ID = "a7.live.probe"

A7_MANIFEST = AdapterManifest(
    adapter_id=A7_ADAPTER_ID,
    name="A7 Live Probe (governed)",
    version="0.0.1",
    tier="A7",
    execution_mode="live_transport",
    parameters=("target",),
    allowed_target_types=("domain",),
    network_access=True,
    fixture_only=False,
    reviewed=True,
    description="Governed live transport prototype — blocked unless a7_live_adapter flag is enabled.",
)


@dataclass(frozen=True)
class A7GateResult:
    allowed: bool
    reason: str
    manifest: AdapterManifest | None

    def to_dict(self) -> dict[str, object]:
        return {
            "allowed": self.allowed,
            "reason": self.reason,
            "manifest": self.manifest.adapter_id if self.manifest else None,
        }


def a7_gate_status() -> A7GateResult:
    if not is_feature_enabled("a7_live_adapter"):
        return A7GateResult(False, "A7 live adapter feature flag is disabled.", None)
    return A7GateResult(True, "A7 manifest registered behind feature flag — still requires ROE + approval.", A7_MANIFEST)


def evaluate_a7_policy(engagement: Engagement, target: str) -> PolicyDecision:
    gate = a7_gate_status()
    if not gate.allowed or gate.manifest is None:
        return PolicyDecision(False, "DENY_A7_DISABLED", gate.reason)
    decision = evaluate_policy(gate.manifest, engagement, target, {"target": target})
    if not decision.allowed and decision.reason_code == REASON_NETWORK_TRANSPORT:
        return PolicyDecision(
            False,
            REASON_NETWORK_TRANSPORT,
            "A7 requires allow_network_transport in rules of engagement.",
            decision.normalized_target,
        )
    return decision