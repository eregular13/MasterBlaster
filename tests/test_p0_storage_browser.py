from datetime import datetime, timezone

from masterblaster_control.p0_approvals import approve_request, request_approval
from masterblaster_control.p0_storage import P0Storage
from masterblaster_control.runner_simulator import RunnerSimulator, build_default_engagement


def _approved_result(storage: P0Storage):
    now = datetime(2026, 1, 1, tzinfo=timezone.utc)
    runner = RunnerSimulator(signing_key=bytes(range(32)))
    engagement = build_default_engagement("example.com", now=now)
    approval = request_approval(engagement, "a2.dns.posture", "example.com", now=now)
    approval = approve_request(approval, now=now)
    result = runner.run(
        "a2.dns.posture",
        "example.com",
        engagement=engagement,
        approval=approval,
        now=now,
    )
    storage.record_runner_result(result)
    return result


def test_storage_lists_engagements_and_filters_audit_events():
    storage = P0Storage(":memory:")
    storage.initialize()
    _approved_result(storage)

    engagements = storage.list_engagements()
    assert len(engagements) == 1
    assert engagements[0]["engagement_id"] == "engagement-local-simulator"
    assert engagements[0]["scope"] == ["example.com"]

    audit_events = storage.list_audit_events(action="runner.completed")
    assert len(audit_events) == 1
    assert audit_events[0]["reason_code"] == "ALLOW"

    filtered = storage.list_audit_events(search="a2.dns.posture")
    assert len(filtered) == 1


def test_storage_filters_evidence_by_adapter_and_search():
    storage = P0Storage(":memory:")
    storage.initialize()
    result = _approved_result(storage)

    records = storage.list_evidence(adapter_id="a2.dns.posture")
    assert len(records) == 1
    assert records[0]["adapter_id"] == "a2.dns.posture"
    assert records[0]["sha256"] == result.evidence[0].sha256

    missing = storage.list_evidence(adapter_id="a0.fixture.inventory")
    assert missing == []