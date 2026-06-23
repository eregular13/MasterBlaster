from datetime import datetime, timezone

from masterblaster_control.p0_approvals import approve_request, deny_request, request_approval
from masterblaster_control.p0_policy import REASON_ALLOW, REASON_TARGET_OUT_OF_SCOPE
from masterblaster_control.p0_retention import RetentionPolicy
from masterblaster_control.p0_storage import P0Storage
from masterblaster_control.runner_simulator import RunnerSimulator, build_default_engagement


def test_storage_records_completed_runner_result():
    now = datetime(2026, 1, 1, tzinfo=timezone.utc)
    runner = RunnerSimulator(signing_key=bytes(range(32)))
    engagement = build_default_engagement("example.com", now=now)
    approval = approve_request(request_approval(engagement, "a0.fixture.inventory", "example.com", now=now), now=now)
    result = runner.run("a0.fixture.inventory", "example.com", engagement=engagement, approval=approval, now=now)
    storage = P0Storage(":memory:")

    storage.record_runner_result(result)
    snapshot = storage.snapshot()
    evidence = storage.list_evidence()
    audit_events = storage.list_audit_events()

    assert result.decision.reason_code == REASON_ALLOW
    assert snapshot.tenants == 1
    assert snapshot.clients == 1
    assert snapshot.engagements == 1
    assert snapshot.approvals == 1
    assert snapshot.jobs == 1
    assert snapshot.evidence_records == 1
    assert snapshot.audit_events == 1
    assert evidence[0]["sha256"] == result.evidence[0].sha256
    assert audit_events[0]["reason_code"] == REASON_ALLOW


def test_storage_records_denied_runner_result_without_job_or_evidence():
    now = datetime(2026, 1, 1, tzinfo=timezone.utc)
    runner = RunnerSimulator(signing_key=bytes(range(32)))
    engagement = build_default_engagement("example.com", now=now)
    result = runner.run("a0.fixture.inventory", "other.example", engagement=engagement, now=now)
    storage = P0Storage(":memory:")

    storage.record_runner_result(result)
    snapshot = storage.snapshot()
    audit_events = storage.list_audit_events()

    assert result.decision.reason_code == REASON_TARGET_OUT_OF_SCOPE
    assert snapshot.tenants == 1
    assert snapshot.clients == 1
    assert snapshot.engagements == 1
    assert snapshot.approvals == 0
    assert snapshot.jobs == 0
    assert snapshot.evidence_records == 0
    assert snapshot.audit_events == 1
    assert audit_events[0]["action"] == "runner.denied"
    assert audit_events[0]["reason_code"] == REASON_TARGET_OUT_OF_SCOPE


def test_storage_records_denied_human_approval_artifact():
    now = datetime(2026, 1, 1, tzinfo=timezone.utc)
    runner = RunnerSimulator(signing_key=bytes(range(32)))
    engagement = build_default_engagement("example.com", now=now)
    approval = deny_request(request_approval(engagement, "a0.fixture.inventory", "example.com", now=now), now=now)
    result = runner.run("a0.fixture.inventory", "example.com", engagement=engagement, approval=approval, now=now)
    storage = P0Storage(":memory:")

    storage.record_runner_result(result)
    snapshot = storage.snapshot()
    audit_events = storage.list_audit_events()

    assert snapshot.approvals == 1
    assert snapshot.jobs == 0
    assert snapshot.audit_events == 1
    assert audit_events[0]["details"]["approval_id"] == approval.approval_id
    assert audit_events[0]["details"]["approval_state"] == "denied"


def test_storage_retention_purges_old_approval_job_evidence_and_audit():
    old_now = datetime(2026, 1, 1, tzinfo=timezone.utc)
    purge_now = datetime(2030, 1, 1, tzinfo=timezone.utc)
    runner = RunnerSimulator(signing_key=bytes(range(32)))
    engagement = build_default_engagement("example.com", now=old_now)
    approval = approve_request(
        request_approval(engagement, "a0.fixture.inventory", "example.com", now=old_now),
        now=old_now,
    )
    result = runner.run("a0.fixture.inventory", "example.com", engagement=engagement, approval=approval, now=old_now)
    storage = P0Storage(":memory:")
    storage.record_runner_result(result)

    retention = storage.apply_retention(RetentionPolicy(1, 1, 1, 1), now=purge_now)
    snapshot = storage.snapshot()

    assert retention.evidence_deleted == 1
    assert retention.jobs_deleted == 1
    assert retention.approvals_deleted == 1
    assert retention.audit_events_deleted == 1
    assert snapshot.approvals == 0
    assert snapshot.jobs == 0
    assert snapshot.evidence_records == 0
    assert snapshot.audit_events == 0
    assert snapshot.engagements == 1
