from __future__ import annotations

from datetime import datetime, timedelta, timezone

from .p0_models import Engagement, RulesOfEngagement, ScopeTarget
from .p0_storage import P0Storage
from .runner_simulator import build_default_engagement


def list_engagement_choices(storage: P0Storage) -> list[tuple[str, str]]:
    rows = storage.list_engagements(limit=100)
    choices = [("Default Local Simulator", "")]
    for row in rows:
        scope = ", ".join(row.get("scope", []))
        label = f"{row['engagement_id']} ({scope})"
        choices.append((label, row["engagement_id"]))
    return choices


def resolve_engagement(storage: P0Storage, engagement_id: str | None, target: str) -> Engagement:
    if not engagement_id:
        return build_default_engagement(target)
    row = storage.get_engagement(engagement_id)
    if not row:
        return build_default_engagement(target)
    return storage.engagement_to_model(row)


def update_engagement_scope(
    storage: P0Storage,
    engagement_id: str,
    scope_patterns: list[str],
    expires_minutes: int,
) -> Engagement:
    row = storage.get_engagement(engagement_id)
    if not row:
        raise ValueError(f"Unknown engagement: {engagement_id}")
    now = datetime.now(timezone.utc)
    engagement = Engagement(
        engagement_id=engagement_id,
        tenant_id=row["tenant_id"],
        client_id=row["client_id"],
        authorized_targets=tuple(ScopeTarget(pattern=item) for item in scope_patterns),
        rules=RulesOfEngagement(
            allow_network_transport=bool(row.get("rules", {}).get("allow_network_transport", False)),
            max_runtime_seconds=int(row.get("rules", {}).get("max_runtime_seconds", 30)),
            notes=str(row.get("rules", {}).get("notes", "")),
        ),
        expires_at=now.replace(microsecond=0) + timedelta(minutes=expires_minutes),
    )
    storage.save_engagement(engagement)
    return engagement