from datetime import datetime, timezone

from masterblaster_control.p0_approvals import approve_request, request_approval
from masterblaster_control.p0_policy import REASON_ALLOW, REASON_APPROVAL_REQUIRED, REASON_TARGET_OUT_OF_SCOPE, canonical_json
from masterblaster_control.runner_simulator import RunnerSimulator, build_default_engagement
from hashlib import sha256


def _approved(engagement, adapter_id, target, now):
    approval = request_approval(engagement, adapter_id, target, now=now)
    return approve_request(approval, now=now)


def test_runner_emits_deterministic_hashed_fixture_evidence():
    now = datetime(2026, 1, 1, tzinfo=timezone.utc)
    runner = RunnerSimulator(signing_key=bytes(range(32)))
    engagement = build_default_engagement("example.com", now=now)
    approval = _approved(engagement, "a0.fixture.inventory", "example.com", now)

    first = runner.run("a0.fixture.inventory", "example.com", engagement=engagement, approval=approval, now=now)
    second = runner.run("a0.fixture.inventory", "example.com", engagement=engagement, approval=approval, now=now)

    assert first.status == "completed"
    assert first.decision.reason_code == REASON_ALLOW
    assert len(first.evidence) == 1
    assert first.evidence[0].sha256 == second.evidence[0].sha256

    expected_hash = sha256(canonical_json(first.evidence[0].content).encode("utf-8")).hexdigest()
    assert first.evidence[0].sha256 == expected_hash


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


def test_dns_posture_fixture_completes_for_domain_target():
    now = datetime(2026, 1, 1, tzinfo=timezone.utc)
    runner = RunnerSimulator(signing_key=bytes(range(32)))
    engagement = build_default_engagement("example.com", now=now)
    approval = _approved(engagement, "a2.dns.posture", "example.com", now)

    result = runner.run("a2.dns.posture", "example.com", engagement=engagement, approval=approval, now=now)

    assert result.status == "completed"
    assert result.decision.reason_code == REASON_ALLOW
    assert result.evidence[0].content["transport"] == "none"
    observation_ids = {item["id"] for item in result.evidence[0].content["observations"]}
    assert "dns.spf" in observation_ids
    assert "dns.dmarc" in observation_ids


def test_http_headers_fixture_completes_for_url_target():
    now = datetime(2026, 1, 1, tzinfo=timezone.utc)
    runner = RunnerSimulator(signing_key=bytes(range(32)))
    target = "https://example.com/"
    engagement = build_default_engagement(target, now=now)
    approval = _approved(engagement, "a3.http.headers", target, now)

    result = runner.run("a3.http.headers", target, engagement=engagement, approval=approval, now=now)

    assert result.status == "completed"
    observation_ids = {item["id"] for item in result.evidence[0].content["observations"]}
    assert "http.strict_transport_security" in observation_ids


def test_tls_cert_expiry_fixture_completes_for_domain_target():
    now = datetime(2026, 1, 1, tzinfo=timezone.utc)
    runner = RunnerSimulator(signing_key=bytes(range(32)))
    engagement = build_default_engagement("example.com", now=now)
    approval = _approved(engagement, "a4.tls.cert_expiry", "example.com", now)

    result = runner.run("a4.tls.cert_expiry", "example.com", engagement=engagement, approval=approval, now=now)

    assert result.status == "completed"
    assert result.evidence[0].content["transport"] == "fake"
    observation_ids = {item["id"] for item in result.evidence[0].content["observations"]}
    assert "tls.certificate.expired" in observation_ids
