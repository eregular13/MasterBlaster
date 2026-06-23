from datetime import datetime, timedelta, timezone

from masterblaster_control.p0_models import Engagement, RulesOfEngagement, ScopeTarget
from masterblaster_control.p7_workflow_generator import (
    generate_workflow_draft,
    workflow_draft_markdown,
)


def test_workflow_draft_is_non_executing_and_ordered():
    now = datetime(2026, 6, 22, tzinfo=timezone.utc)
    engagement = Engagement(
        engagement_id="engagement-v1",
        tenant_id="tenant-v1",
        client_id="client-v1",
        authorized_targets=(ScopeTarget(pattern="example.com"),),
        rules=RulesOfEngagement(),
        expires_at=now + timedelta(hours=2),
    )
    draft = generate_workflow_draft(engagement)
    markdown = workflow_draft_markdown(draft)

    assert draft.steps
    assert draft.steps[0].adapter_id == "a0.fixture.inventory"
    assert all(step.requires_approval for step in draft.steps)
    assert "WORKFLOW DRAFT ONLY" in markdown
    assert "a5.port.scan_sim" in {step.adapter_id for step in draft.steps}