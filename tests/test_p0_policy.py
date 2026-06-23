from dataclasses import replace
from datetime import datetime, timedelta, timezone

from masterblaster_control.p0_models import Engagement, RulesOfEngagement, ScopeTarget
from masterblaster_control.p0_policy import (
    REASON_ALLOW,
    REASON_BAD_SIGNATURE,
    REASON_EXPIRED_ENGAGEMENT,
    REASON_TARGET_OUT_OF_SCOPE,
    REASON_TARGET_TYPE,
    REASON_UNKNOWN_ADAPTER,
    REASON_UNKNOWN_ARGUMENT,
    evaluate_policy,
    sign_job_envelope,
    validate_job_envelope,
)
from masterblaster_control.runner_simulator import MANIFESTS, RunnerSimulator, build_default_engagement


def test_unknown_adapter_denies_by_default():
    engagement = build_default_engagement("example.com")

    decision = evaluate_policy(None, engagement, "example.com")

    assert decision.allowed is False
    assert decision.reason_code == REASON_UNKNOWN_ADAPTER


def test_target_outside_scope_is_denied():
    engagement = build_default_engagement("example.com")
    manifest = MANIFESTS["a0.fixture.inventory"]

    decision = evaluate_policy(manifest, engagement, "other.example")

    assert decision.allowed is False
    assert decision.reason_code == REASON_TARGET_OUT_OF_SCOPE


def test_unknown_arguments_are_denied():
    engagement = build_default_engagement("example.com")
    manifest = MANIFESTS["a0.fixture.inventory"]

    decision = evaluate_policy(manifest, engagement, "example.com", {"target": "example.com", "flags": "-A"})

    assert decision.allowed is False
    assert decision.reason_code == REASON_UNKNOWN_ARGUMENT


def test_tls_adapter_rejects_ip_target_type():
    engagement = build_default_engagement("192.0.2.10")
    manifest = MANIFESTS["a1.tls.assessment"]

    decision = evaluate_policy(manifest, engagement, "192.0.2.10")

    assert decision.allowed is False
    assert decision.reason_code == REASON_TARGET_TYPE


def test_expired_engagement_is_denied():
    now = datetime(2026, 1, 1, tzinfo=timezone.utc)
    engagement = Engagement(
        engagement_id="eng-expired",
        tenant_id="tenant-1",
        client_id="client-1",
        authorized_targets=(ScopeTarget("example.com"),),
        rules=RulesOfEngagement(),
        expires_at=now - timedelta(seconds=1),
    )
    manifest = MANIFESTS["a0.fixture.inventory"]

    decision = evaluate_policy(manifest, engagement, "example.com", now=now)

    assert decision.allowed is False
    assert decision.reason_code == REASON_EXPIRED_ENGAGEMENT


def test_tampered_signed_job_is_denied():
    now = datetime(2026, 1, 1, tzinfo=timezone.utc)
    runner = RunnerSimulator(signing_key=bytes(range(32)))
    result = runner.run("a0.fixture.inventory", "example.com", now=now)
    assert result.decision.reason_code == REASON_ALLOW
    assert result.job is not None

    tampered = replace(result.job, target="other.example")
    engagement = build_default_engagement("example.com", now=now)
    manifest = MANIFESTS["a0.fixture.inventory"]

    decision = validate_job_envelope(tampered, manifest, engagement, bytes(range(32)), now=now)

    assert decision.allowed is False
    assert decision.reason_code == REASON_BAD_SIGNATURE
