from dataclasses import replace
from datetime import datetime, timedelta, timezone

import pytest

from masterblaster_control.p0_approvals import approve_request, request_approval
from masterblaster_control.p0_models import Engagement, RulesOfEngagement, ScopeTarget
from masterblaster_control.p0_policy import (
    REASON_ALLOW,
    REASON_BAD_SIGNATURE,
    REASON_EXPIRED_ENGAGEMENT,
    REASON_JOB_ARGUMENT_TARGET_MISMATCH,
    REASON_JOB_CLIENT_MISMATCH,
    REASON_JOB_TTL_EXCEEDED,
    REASON_TARGET_OUT_OF_SCOPE,
    REASON_TARGET_TYPE,
    REASON_UNKNOWN_ADAPTER,
    REASON_UNKNOWN_ARGUMENT,
    evaluate_policy,
    parse_target,
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


def test_url_targets_reject_secret_or_ambiguous_components():
    for target in (
        "https://user@example.com/",
        "https://user:password@example.com/",
        "https://example.com/path?token=abc123",
        "https://example.com/path#fragment",
    ):
        with pytest.raises(Exception, match="URL targets must not include"):
            parse_target(target)


@pytest.mark.parametrize(
    "target",
    [
        "https://[::1",
        "https://example.com:bad/",
        "https://%65xample.com/",
        "https://example.com/%2e%2e",
        "https://exa\u043cple.com/",
        "https://example.com/\x00",
    ],
)
def test_malformed_or_ambiguous_targets_fail_policy_closed(target):
    engagement = build_default_engagement("example.com")
    manifest = MANIFESTS["a0.fixture.inventory"]

    decision = evaluate_policy(manifest, engagement, target)

    assert decision.allowed is False


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
    engagement = build_default_engagement("example.com", now=now)
    approval = approve_request(request_approval(engagement, "a0.fixture.inventory", "example.com", now=now), now=now)
    result = runner.run("a0.fixture.inventory", "example.com", engagement=engagement, approval=approval, now=now)
    assert result.decision.reason_code == REASON_ALLOW
    assert result.job is not None

    tampered = replace(result.job, target="other.example")
    manifest = MANIFESTS["a0.fixture.inventory"]

    decision = validate_job_envelope(tampered, manifest, engagement, bytes(range(32)), now=now)

    assert decision.allowed is False
    assert decision.reason_code == REASON_BAD_SIGNATURE


def test_signed_job_with_cross_client_binding_is_denied():
    now = datetime(2026, 1, 1, tzinfo=timezone.utc)
    runner = RunnerSimulator(signing_key=bytes(range(32)))
    engagement = build_default_engagement("example.com", now=now)
    approval = approve_request(request_approval(engagement, "a0.fixture.inventory", "example.com", now=now), now=now)
    result = runner.run("a0.fixture.inventory", "example.com", engagement=engagement, approval=approval, now=now)
    assert result.job is not None
    mismatched = sign_job_envelope(replace(result.job, client_id="client-other", signature=""), bytes(range(32)))

    decision = validate_job_envelope(mismatched, MANIFESTS["a0.fixture.inventory"], engagement, bytes(range(32)), now=now)

    assert decision.allowed is False
    assert decision.reason_code == REASON_JOB_CLIENT_MISMATCH


def test_signed_job_with_target_argument_mismatch_is_denied():
    now = datetime(2026, 1, 1, tzinfo=timezone.utc)
    runner = RunnerSimulator(signing_key=bytes(range(32)))
    engagement = build_default_engagement("example.com", now=now)
    approval = approve_request(request_approval(engagement, "a0.fixture.inventory", "example.com", now=now), now=now)
    result = runner.run("a0.fixture.inventory", "example.com", engagement=engagement, approval=approval, now=now)
    assert result.job is not None
    mismatched = sign_job_envelope(
        replace(result.job, arguments={"target": "other.example"}, signature=""),
        bytes(range(32)),
    )

    decision = validate_job_envelope(mismatched, MANIFESTS["a0.fixture.inventory"], engagement, bytes(range(32)), now=now)

    assert decision.allowed is False
    assert decision.reason_code == REASON_JOB_ARGUMENT_TARGET_MISMATCH


def test_signed_job_ttl_cannot_exceed_rules_of_engagement():
    now = datetime(2026, 1, 1, tzinfo=timezone.utc)
    runner = RunnerSimulator(signing_key=bytes(range(32)))
    engagement = build_default_engagement("example.com", now=now)
    approval = approve_request(request_approval(engagement, "a0.fixture.inventory", "example.com", now=now), now=now)
    result = runner.run("a0.fixture.inventory", "example.com", engagement=engagement, approval=approval, now=now)
    assert result.job is not None
    overlong = sign_job_envelope(
        replace(result.job, expires_at=now + timedelta(seconds=engagement.rules.max_runtime_seconds + 1), signature=""),
        bytes(range(32)),
    )

    decision = validate_job_envelope(overlong, MANIFESTS["a0.fixture.inventory"], engagement, bytes(range(32)), now=now)

    assert decision.allowed is False
    assert decision.reason_code == REASON_JOB_TTL_EXCEEDED
