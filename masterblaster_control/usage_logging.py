"""Billable usage logging for engagements — supports invoicing and margin analysis."""

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from .p0_storage import P0Storage


@dataclass(frozen=True)
class UsageEvent:
    event_id: str
    tenant_id: str
    client_id: str
    engagement_id: str
    event_type: str
    quantity: float
    unit: str
    metadata: dict[str, Any]
    created_at: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "event_id": self.event_id,
            "tenant_id": self.tenant_id,
            "client_id": self.client_id,
            "engagement_id": self.engagement_id,
            "event_type": self.event_type,
            "quantity": self.quantity,
            "unit": self.unit,
            "metadata": self.metadata,
            "created_at": self.created_at,
        }


def log_usage(
    storage: P0Storage,
    *,
    tenant_id: str,
    client_id: str,
    engagement_id: str,
    event_type: str,
    quantity: float = 1.0,
    unit: str = "operation",
    metadata: dict[str, Any] | None = None,
) -> UsageEvent:
    """Record a billable usage event (MCP run, report export, tool invocation, etc.)."""
    storage.ensure_usage_schema()
    now = datetime.now(timezone.utc).isoformat()
    event = UsageEvent(
        event_id=f"usage-{uuid.uuid4().hex[:16]}",
        tenant_id=tenant_id,
        client_id=client_id,
        engagement_id=engagement_id,
        event_type=event_type,
        quantity=quantity,
        unit=unit,
        metadata=metadata or {},
        created_at=now,
    )
    storage.insert_usage_event(event.to_dict())
    return event


def usage_summary_markdown(storage: P0Storage, engagement_id: str | None = None) -> str:
    rows = storage.list_usage_events(engagement_id=engagement_id, limit=500)
    totals: dict[str, float] = {}
    for row in rows:
        key = row["event_type"]
        totals[key] = totals.get(key, 0.0) + float(row["quantity"])
    lines = [
        "# Usage Summary",
        "",
        f"**Events recorded:** {len(rows)}",
        "",
        "| Event Type | Quantity |",
        "| --- | ---: |",
    ]
    for event_type, quantity in sorted(totals.items()):
        lines.append(f"| {event_type} | {quantity:g} |")
    return "\n".join(lines)


def export_usage_csv(storage: P0Storage, engagement_id: str | None = None) -> str:
    rows = storage.list_usage_events(engagement_id=engagement_id, limit=2000)
    lines = ["event_id,tenant_id,client_id,engagement_id,event_type,quantity,unit,created_at,metadata"]
    for row in rows:
        metadata = json.dumps(row.get("metadata", {}), sort_keys=True)
        lines.append(
            ",".join(
                f'"{str(row.get(col, "")).replace(chr(34), chr(34) * 2)}"'
                for col in (
                    "event_id",
                    "tenant_id",
                    "client_id",
                    "engagement_id",
                    "event_type",
                    "quantity",
                    "unit",
                    "created_at",
                )
            )
            + f',"{metadata.replace(chr(34), chr(34) * 2)}"'
        )
    return "\n".join(lines) + "\n"