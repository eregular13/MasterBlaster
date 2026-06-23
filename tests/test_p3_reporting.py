from datetime import datetime, timezone

from masterblaster_control.p0_approvals import approve_request, request_approval
from masterblaster_control.p3_reporting import (
    compliance_draft_markdown,
    generate_compliance_draft,
    project_findings_from_evidence,
)
from masterblaster_control.p0_storage import P0Storage
from masterblaster_control.runner_simulator import RunnerSimulator, build_default_engagement


def test_findings_projection_and_compliance_draft():
    storage = P0Storage(":memory:")
    storage.initialize()
    now = datetime(2026, 1, 1, tzinfo=timezone.utc)
    runner = RunnerSimulator(signing_key=bytes(range(32)))
    engagement = build_default_engagement("example.com", now=now)
    approval = approve_request(
        request_approval(engagement, "a2.dns.posture", "example.com", now=now),
        now=now,
    )
    result = runner.run("a2.dns.posture", "example.com", engagement=engagement, approval=approval, now=now)
    storage.record_runner_result(result)

    findings = project_findings_from_evidence(result.evidence)
    assert findings
    draft = generate_compliance_draft(storage)
    markdown = compliance_draft_markdown(draft)
    assert "SIMULATOR DRAFT ONLY" in markdown
    assert draft.evidence_ids