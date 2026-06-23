from dataclasses import replace

from masterblaster_control.p0_models import RulesOfEngagement
from masterblaster_control.p0_policy import REASON_NETWORK_TRANSPORT
from masterblaster_control.p9_a7_adapter import a7_gate_status, evaluate_a7_policy
from masterblaster_control.runner_simulator import build_default_engagement


def test_a7_gate_disabled_by_default():
    gate = a7_gate_status()
    assert gate.allowed is False
    assert gate.manifest is None


def test_a7_policy_denies_when_disabled():
    engagement = build_default_engagement("example.com")
    decision = evaluate_a7_policy(engagement, "example.com")
    assert decision.allowed is False
    assert decision.reason_code == "DENY_A7_DISABLED"


def test_a7_policy_checks_network_roe_when_enabled(monkeypatch, tmp_path):
    config = tmp_path / "feature_flags.json"
    config.write_text('{"flags": {"a7_live_adapter": true}}', encoding="utf-8")
    monkeypatch.setenv("MB_FEATURE_A7_LIVE_ADAPTER", "true")

    engagement = replace(
        build_default_engagement("example.com"),
        rules=RulesOfEngagement(allow_network_transport=False),
    )
    decision = evaluate_a7_policy(engagement, "example.com")
    assert decision.allowed is False
    assert decision.reason_code == REASON_NETWORK_TRANSPORT