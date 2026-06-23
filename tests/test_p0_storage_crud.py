import json
from datetime import datetime, timedelta, timezone

from masterblaster_control.p0_models import Engagement, RulesOfEngagement, ScopeTarget
from masterblaster_control.p0_storage import P0Storage


def test_storage_crud_for_tenant_client_and_engagement():
    storage = P0Storage(":memory:")
    storage.initialize()

    storage.create_tenant("tenant-alpha", "Alpha Tenant")
    storage.create_client("client-alpha", "tenant-alpha", "Alpha Client")

    now = datetime(2026, 2, 1, tzinfo=timezone.utc)
    engagement = Engagement(
        engagement_id="engagement-alpha",
        tenant_id="tenant-alpha",
        client_id="client-alpha",
        authorized_targets=(ScopeTarget(pattern="alpha.example"),),
        rules=RulesOfEngagement(allow_network_transport=False, max_runtime_seconds=30),
        expires_at=now + timedelta(hours=2),
    )
    storage.save_engagement(engagement)

    tenants = storage.list_tenants()
    clients = storage.list_clients(tenant_id="tenant-alpha")
    engagements = storage.list_engagements(tenant_id="tenant-alpha")

    assert len(tenants) == 1
    assert tenants[0]["display_name"] == "Alpha Tenant"
    assert len(clients) == 1
    assert clients[0]["client_id"] == "client-alpha"
    assert len(engagements) == 1
    assert engagements[0]["scope"] == ["alpha.example"]


def test_storage_exports_and_evidence_lookup():
    storage = P0Storage(":memory:")
    storage.initialize()
    storage.create_tenant("tenant-beta", "Beta Tenant")
    storage.create_client("client-beta", "tenant-beta", "Beta Client")
    now = datetime(2026, 2, 1, tzinfo=timezone.utc)
    storage.save_engagement(
        Engagement(
            engagement_id="engagement-beta",
            tenant_id="tenant-beta",
            client_id="client-beta",
            authorized_targets=(ScopeTarget(pattern="beta.example"),),
            rules=RulesOfEngagement(),
            expires_at=now + timedelta(hours=1),
        )
    )

    from masterblaster_control.p0_approvals import approve_request, request_approval
    from masterblaster_control.runner_simulator import RunnerSimulator

    runner = RunnerSimulator(signing_key=bytes(range(32)))
    engagement = storage.list_engagements()[0]
    built = Engagement(
        engagement_id=engagement["engagement_id"],
        tenant_id=engagement["tenant_id"],
        client_id=engagement["client_id"],
        authorized_targets=(ScopeTarget(pattern="beta.example"),),
        rules=RulesOfEngagement(),
        expires_at=now + timedelta(hours=1),
    )
    approval = approve_request(
        request_approval(built, "a2.dns.posture", "beta.example", now=now),
        now=now,
    )
    result = runner.run("a2.dns.posture", "beta.example", engagement=built, approval=approval, now=now)
    storage.record_runner_result(result)

    evidence_id = result.evidence[0].evidence_id
    fetched = storage.get_evidence(evidence_id)
    assert fetched is not None
    assert fetched["sha256"] == result.evidence[0].sha256

    csv_export = storage.export_audit_events_csv()
    assert "event_id,tenant_id,engagement_id,action,reason_code,created_at,details" in csv_export
    json_export = storage.export_evidence_json()
    payload = json.loads(json_export)
    assert payload[0]["evidence_id"] == evidence_id


def test_delete_engagement_cascades_related_records():
    storage = P0Storage(":memory:")
    storage.initialize()
    from masterblaster_control.p0_approvals import approve_request, request_approval
    from masterblaster_control.runner_simulator import RunnerSimulator, build_default_engagement

    now = datetime(2026, 2, 1, tzinfo=timezone.utc)
    runner = RunnerSimulator(signing_key=bytes(range(32)))
    engagement = build_default_engagement("example.com", now=now)
    approval = approve_request(
        request_approval(engagement, "a0.fixture.inventory", "example.com", now=now),
        now=now,
    )
    result = runner.run("a0.fixture.inventory", "example.com", engagement=engagement, approval=approval, now=now)
    storage.record_runner_result(result)
    assert storage.delete_engagement("engagement-local-simulator") == 1
    assert storage.list_engagements() == []


def test_storage_filters_evidence_by_job_id():
    storage = P0Storage(":memory:")
    storage.initialize()
    from masterblaster_control.p0_approvals import approve_request, request_approval
    from masterblaster_control.runner_simulator import RunnerSimulator, build_default_engagement

    now = datetime(2026, 2, 1, tzinfo=timezone.utc)
    runner = RunnerSimulator(signing_key=bytes(range(32)))
    engagement = build_default_engagement("example.com", now=now)
    approval = approve_request(
        request_approval(engagement, "a0.fixture.inventory", "example.com", now=now),
        now=now,
    )
    result = runner.run("a0.fixture.inventory", "example.com", engagement=engagement, approval=approval, now=now)
    storage.record_runner_result(result)

    records = storage.list_evidence(job_id=result.job.job_id)
    assert len(records) == 1
    assert records[0]["job_id"] == result.job.job_id