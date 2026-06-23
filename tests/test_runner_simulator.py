from dataclasses import replace
from datetime import datetime, timezone

import pytest

from masterblaster_control.p0_approvals import approve_request, request_approval
from masterblaster_control.p0_policy import (
    REASON_ALLOW,
    REASON_APPROVAL_REPLAY,
    REASON_APPROVAL_REQUIRED,
    REASON_TARGET_OUT_OF_SCOPE,
)
from masterblaster_control.runner_simulator import (
    ADAPTER_HANDLERS,
    MANIFESTS,
    RunnerSimulator,
    build_default_engagement,
    evidence_digest,
    validate_adapter_handler_registry,
    verify_evidence_record,
)


def _approved(engagement, adapter_id, target, now):
    approval = request_approval(engagement, adapter_id, target, now=now)
    return approve_request(approval, now=now)


def test_runner_emits_deterministic_hashed_fixture_evidence():
    now = datetime(2026, 1, 1, tzinfo=timezone.utc)
    first_runner = RunnerSimulator(signing_key=bytes(range(32)), job_id_factory=lambda: "job-fixed")
    second_runner = RunnerSimulator(signing_key=bytes(range(32)), job_id_factory=lambda: "job-fixed")
    engagement = build_default_engagement("example.com", now=now)
    approval = replace(_approved(engagement, "a0.fixture.inventory", "example.com", now), approval_id="approval-fixed")

    first = first_runner.run("a0.fixture.inventory", "example.com", engagement=engagement, approval=approval, now=now)
    second = second_runner.run("a0.fixture.inventory", "example.com", engagement=engagement, approval=approval, now=now)

    assert first.status == "completed"
    assert first.decision.reason_code == REASON_ALLOW
    assert len(first.evidence) == 1
    assert first.evidence[0].sha256 == second.evidence[0].sha256
    assert first.evidence[0].approval_id == "approval-fixed"
    assert first.evidence[0].fixture_id == "a0.fixture.inventory:healthy:v1"
    assert first.job is not None
    assert verify_evidence_record(first.evidence[0], first.job) is True
    assert first.evidence[0].sha256 == evidence_digest(first.evidence[0])


def test_runner_rejects_approval_replay_inside_runner_instance():
    now = datetime(2026, 1, 1, tzinfo=timezone.utc)
    runner = RunnerSimulator(signing_key=bytes(range(32)))
    engagement = build_default_engagement("example.com", now=now)
    approval = _approved(engagement, "a0.fixture.inventory", "example.com", now)

    first = runner.run("a0.fixture.inventory", "example.com", engagement=engagement, approval=approval, now=now)
    second = runner.run("a0.fixture.inventory", "example.com", engagement=engagement, approval=approval, now=now)

    assert first.status == "completed"
    assert second.status == "denied"
    assert second.decision.reason_code == REASON_APPROVAL_REPLAY
    assert second.job is None
    assert second.evidence == ()


def test_runner_requires_human_approval_before_issuing_job():
    now = datetime(2026, 1, 1, tzinfo=timezone.utc)
    runner = RunnerSimulator(signing_key=bytes(range(32)))

    result = runner.run("a0.fixture.inventory", "example.com", now=now)

    assert result.status == "denied"
    assert result.job is None
    assert result.evidence == ()
    assert result.decision.reason_code == REASON_APPROVAL_REQUIRED


def test_runner_denies_out_of_scope_target_before_issuing_job():
    now = datetime(2026, 1, 1, tzinfo=timezone.utc)
    runner = RunnerSimulator(signing_key=bytes(range(32)))
    engagement = build_default_engagement("example.com", now=now)

    result = runner.run("a0.fixture.inventory", "other.example", engagement=engagement, now=now)

    assert result.status == "denied"
    assert result.job is None
    assert result.evidence == ()
    assert result.decision.reason_code == REASON_TARGET_OUT_OF_SCOPE


def test_tls_fake_transport_completes_for_domain_target():
    now = datetime(2026, 1, 1, tzinfo=timezone.utc)
    runner = RunnerSimulator(signing_key=bytes(range(32)))
    engagement = build_default_engagement("example.com", now=now)
    approval = _approved(engagement, "a1.tls.assessment", "example.com", now)

    result = runner.run("a1.tls.assessment", "example.com", engagement=engagement, approval=approval, now=now)

    assert result.status == "completed"
    assert result.decision.reason_code == REASON_ALLOW
    assert result.evidence[0].content["transport"] == "fake"


@pytest.mark.parametrize(
    ("adapter_id", "target", "scenario"),
    [
        ("a2.http.headers", "https://example.com/", "weak"),
        ("a2.dns.posture", "example.com", "weak"),
        ("a2.certificate.expiry", "example.com", "weak"),
    ],
)
def test_additional_fixture_adapters_emit_verified_evidence(adapter_id, target, scenario):
    now = datetime(2026, 1, 1, tzinfo=timezone.utc)
    runner = RunnerSimulator(signing_key=bytes(range(32)))
    engagement = build_default_engagement(target, now=now)
    approval = _approved(engagement, adapter_id, target, now)

    result = runner.run(
        adapter_id,
        target,
        engagement=engagement,
        approval=approval,
        arguments={"scenario": scenario},
        now=now,
    )

    assert result.status == "completed"
    assert result.job is not None
    assert result.evidence[0].fixture_id == f"{adapter_id}:{scenario}:v1"
    assert result.evidence[0].content["parser"]["status"] == "accepted"
    assert verify_evidence_record(result.evidence[0], result.job) is True


@pytest.mark.parametrize("scenario", ["malformed", "unsupported_schema", "unexpected_observation"])
def test_fixture_parser_rejects_bad_scenarios_without_network(scenario):
    now = datetime(2026, 1, 1, tzinfo=timezone.utc)
    runner = RunnerSimulator(signing_key=bytes(range(32)))
    engagement = build_default_engagement("https://example.com/", now=now)
    approval = _approved(engagement, "a2.http.headers", "https://example.com/", now)

    result = runner.run(
        "a2.http.headers",
        "https://example.com/",
        engagement=engagement,
        approval=approval,
        arguments={"scenario": scenario},
        now=now,
    )

    assert result.status == "completed"
    assert result.evidence[0].content["parser"]["status"] == "rejected"
    assert result.evidence[0].content["parser"]["errors"]


def test_evidence_verifier_rejects_metadata_substitution():
    now = datetime(2026, 1, 1, tzinfo=timezone.utc)
    runner = RunnerSimulator(signing_key=bytes(range(32)))
    engagement = build_default_engagement("example.com", now=now)
    approval = _approved(engagement, "a0.fixture.inventory", "example.com", now)
    result = runner.run("a0.fixture.inventory", "example.com", engagement=engagement, approval=approval, now=now)

    swapped = replace(result.evidence[0], parser_version="2.0.0")

    assert verify_evidence_record(swapped, result.job) is False


def test_manifest_registry_is_immutable_to_callers():
    with pytest.raises(TypeError):
        MANIFESTS["evil.live.adapter"] = MANIFESTS["a0.fixture.inventory"]  # type: ignore[index]


def test_adapter_handler_registry_is_immutable_and_complete():
    with pytest.raises(TypeError):
        ADAPTER_HANDLERS["evil.live.adapter"] = next(iter(ADAPTER_HANDLERS.values()))  # type: ignore[index]

    assert validate_adapter_handler_registry() == ()
