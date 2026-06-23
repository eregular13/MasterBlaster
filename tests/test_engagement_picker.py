from datetime import datetime, timedelta, timezone

from masterblaster_control.engagement_picker import list_engagement_choices, resolve_engagement, update_engagement_scope
from masterblaster_control.p0_models import Engagement, RulesOfEngagement, ScopeTarget
from masterblaster_control.p0_storage import P0Storage


def test_engagement_picker_lists_and_resolves_custom_engagement():
    storage = P0Storage(":memory:")
    storage.initialize()
    now = datetime(2026, 3, 1, tzinfo=timezone.utc)
    storage.save_engagement(
        Engagement(
            engagement_id="eng-custom",
            tenant_id="tenant-custom",
            client_id="client-custom",
            authorized_targets=(ScopeTarget(pattern="custom.example"),),
            rules=RulesOfEngagement(),
            expires_at=now + timedelta(hours=1),
        )
    )
    choices = list_engagement_choices(storage)
    assert any(item[1] == "eng-custom" for item in choices)
    engagement = resolve_engagement(storage, "eng-custom", "custom.example")
    assert engagement.engagement_id == "eng-custom"


def test_update_engagement_scope():
    storage = P0Storage(":memory:")
    storage.initialize()
    now = datetime(2026, 3, 1, tzinfo=timezone.utc)
    storage.save_engagement(
        Engagement(
            engagement_id="eng-edit",
            tenant_id="tenant-edit",
            client_id="client-edit",
            authorized_targets=(ScopeTarget(pattern="old.example"),),
            rules=RulesOfEngagement(),
            expires_at=now + timedelta(hours=1),
        )
    )
    updated = update_engagement_scope(storage, "eng-edit", ["new.example", "10.0.0.0/24"], expires_minutes=90)
    assert updated.authorized_targets[0].pattern == "new.example"
    row = storage.get_engagement("eng-edit")
    assert "new.example" in row["scope"]