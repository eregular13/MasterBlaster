from datetime import datetime, timedelta, timezone

from masterblaster_control.p0_models import Engagement, RulesOfEngagement, ScopeTarget
from masterblaster_control.p7_workflow_generator import generate_workflow_draft
from masterblaster_control.p8_workflow_assistant import assistant_markdown, enrich_workflow_draft


def test_assistant_enriches_without_executing():
    now = datetime(2026, 6, 23, tzinfo=timezone.utc)
    engagement = Engagement(
        engagement_id="eng-p8",
        tenant_id="tenant-p8",
        client_id="client-p8",
        authorized_targets=(ScopeTarget(pattern="example.com"),),
        rules=RulesOfEngagement(),
        expires_at=now + timedelta(hours=1),
    )
    draft = generate_workflow_draft(engagement)
    enriched = enrich_workflow_draft(draft)
    markdown = assistant_markdown(draft)
    assert len(enriched.steps) == len(draft.steps)
    assert "ASSISTANT ENRICHMENT" in markdown
    assert "Suggested checks" in enriched.steps[0].rationale