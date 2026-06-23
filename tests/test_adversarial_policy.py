"""Adversarial policy scenarios — deny-by-default pen-test pack."""

from dataclasses import replace
from datetime import datetime, timedelta, timezone

import pytest

from masterblaster_control.p0_models import AdapterManifest, Engagement, JobEnvelope, RulesOfEngagement, ScopeTarget
from masterblaster_control.p0_policy import (
    REASON_ALLOW,
    REASON_BAD_SIGNATURE,
    REASON_EXPIRED_ENGAGEMENT,
    REASON_NETWORK_TRANSPORT,
    REASON_TARGET_OUT_OF_SCOPE,
    REASON_UNKNOWN_ADAPTER,
    REASON_UNKNOWN_ARGUMENT,
    evaluate_policy,
    parse_target,
    sign_job_envelope,
    validate_job_envelope,
)
from masterblaster_control.runner_simulator import MANIFESTS, RunnerSimulator, build_default_engagement


def _engagement(target: str = "example.com") -> Engagement:
    return build_default_engagement(target)


def test_adversarial_unknown_adapter_injection():
    decision = evaluate_policy(None, _engagement(), "example.com")

    assert decision.allowed is False
    assert decision.reason_code == REASON_UNKNOWN_ADAPTER


def test_adversarial_scope_hopping():
    manifest = MANIFESTS["a0.fixture.inventory"]

    decision = evaluate_policy(manifest, _engagement("example.com"), "evil.example")

    assert decision.allowed is False
    assert decision.reason_code == REASON_TARGET_OUT_OF_SCOPE


def test_adversarial_credential_smuggling_in_url():
    for target in (
        "https://user@example.com/",
        "https://user:password@example.com/",
        "https://example.com/path?token=abc",
    ):
        with pytest.raises(Exception, match="URL targets must not include"):
            parse_target(target)


def test_adversarial_extra_arguments_blocked():
    manifest = MANIFESTS["a0.fixture.inventory"]

    decision = evaluate_policy(
        manifest,
        _engagement(),
        "example.com",
        {"target": "example.com", "shell": "rm -rf /"},
    )

    assert decision.allowed is False
    assert decision.reason_code == REASON_UNKNOWN_ARGUMENT


def test_adversarial_network_transport_denied_without_roe():
    manifest = AdapterManifest(
        adapter_id="a7.live.probe",
        name="A7 Live Probe (test fixture)",
        version="0.0.1",
        tier="A7",
        execution_mode="live_transport",
        parameters=("target",),
        allowed_target_types=("domain",),
        network_access=True,
        fixture_only=False,
        reviewed=True,
        description="Synthetic manifest for adversarial network-transport denial tests.",
    )
    engagement = replace(
        _engagement(),
        rules=RulesOfEngagement(allow_network_transport=False),
    )

    decision = evaluate_policy(manifest, engagement, "example.com")

    assert decision.allowed is False
    assert decision.reason_code == REASON_NETWORK_TRANSPORT


def test_adversarial_expired_engagement_replay():
    now = datetime(2026, 6, 23, tzinfo=timezone.utc)
    engagement = Engagement(
        engagement_id="eng-replay",
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


def test_adversarial_tampered_job_signature():
    runner = RunnerSimulator()
    engagement = _engagement()
    manifest = MANIFESTS["a0.fixture.inventory"]
    now = datetime(2026, 6, 23, tzinfo=timezone.utc)
    job = JobEnvelope(
        job_id="job-adversarial",
        tenant_id=engagement.tenant_id,
        client_id=engagement.client_id,
        engagement_id=engagement.engagement_id,
        adapter_id=manifest.adapter_id,
        target="example.com",
        arguments={"target": "example.com"},
        issued_at=now,
        expires_at=now + timedelta(seconds=30),
    )
    signed = sign_job_envelope(job, runner._signing_key)
    tampered = replace(signed, signature="0" * 64)

    decision = validate_job_envelope(tampered, manifest, engagement, runner._signing_key, now=now)

    assert decision.allowed is False
    assert decision.reason_code == REASON_BAD_SIGNATURE


def test_adversarial_valid_path_still_allows_simulator_only():
    manifest = MANIFESTS["a0.fixture.inventory"]

    decision = evaluate_policy(manifest, _engagement(), "example.com", {"target": "example.com"})

    assert decision.allowed is True
    assert decision.reason_code == REASON_ALLOW