"""Re-test and validation workflow — tracks remediation verification for follow-on billing."""

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from .p0_models import Finding
from .professional_reporting import ProfessionalReport, SEVERITY_ORDER

RETEST_PATH = Path("data") / "business" / "retest_records.json"


@dataclass(frozen=True)
class RetestItem:
    finding_id: str
    title: str
    original_severity: str
    status: str  # open | remediated | verified | accepted-risk
    retest_notes: str
    verified_at: str | None

    def to_dict(self) -> dict:
        return {
            "finding_id": self.finding_id,
            "title": self.title,
            "original_severity": self.original_severity,
            "status": self.status,
            "retest_notes": self.retest_notes,
            "verified_at": self.verified_at,
        }

    @classmethod
    def from_dict(cls, data: dict) -> RetestItem:
        return cls(
            finding_id=str(data["finding_id"]),
            title=str(data.get("title", "")),
            original_severity=str(data.get("original_severity", "medium")),
            status=str(data.get("status", "open")),
            retest_notes=str(data.get("retest_notes", "")),
            verified_at=data.get("verified_at"),
        )


@dataclass(frozen=True)
class RetestCampaign:
    campaign_id: str
    engagement_id: str
    client_name: str
    project_name: str
    created_at: str
    items: tuple[RetestItem, ...]

    def to_dict(self) -> dict:
        return {
            "campaign_id": self.campaign_id,
            "engagement_id": self.engagement_id,
            "client_name": self.client_name,
            "project_name": self.project_name,
            "created_at": self.created_at,
            "items": [item.to_dict() for item in self.items],
        }


def _load_campaigns() -> list[dict]:
    if not RETEST_PATH.exists():
        return []
    return json.loads(RETEST_PATH.read_text(encoding="utf-8")).get("campaigns", [])


def _save_campaigns(campaigns: list[dict]) -> None:
    RETEST_PATH.parent.mkdir(parents=True, exist_ok=True)
    RETEST_PATH.write_text(json.dumps({"campaigns": campaigns}, indent=2), encoding="utf-8")


def create_retest_campaign(report: ProfessionalReport) -> RetestCampaign:
    """Initialize a re-test campaign from assessment findings."""
    now = datetime.now(timezone.utc).isoformat()
    items = tuple(
        RetestItem(
            finding_id=f.finding_id,
            title=f.title,
            original_severity=f.severity,
            status="open",
            retest_notes="",
            verified_at=None,
        )
        for f in report.findings
    )
    campaign = RetestCampaign(
        campaign_id=f"retest-{uuid.uuid4().hex[:10]}",
        engagement_id=report.engagement_id,
        client_name=report.client_name,
        project_name=report.project_name,
        created_at=now,
        items=items,
    )
    campaigns = _load_campaigns()
    campaigns.append(campaign.to_dict())
    _save_campaigns(campaigns)
    return campaign


def update_retest_item(
    campaign_id: str,
    finding_id: str,
    *,
    status: str,
    notes: str = "",
) -> RetestCampaign | None:
    campaigns = _load_campaigns()
    for index, raw in enumerate(campaigns):
        if raw["campaign_id"] != campaign_id:
            continue
        items = [RetestItem.from_dict(item) for item in raw.get("items", [])]
        updated: list[RetestItem] = []
        now = datetime.now(timezone.utc).isoformat()
        for item in items:
            if item.finding_id == finding_id:
                verified = now if status == "verified" else item.verified_at
                updated.append(
                    RetestItem(
                        finding_id=item.finding_id,
                        title=item.title,
                        original_severity=item.original_severity,
                        status=status,
                        retest_notes=notes or item.retest_notes,
                        verified_at=verified,
                    )
                )
            else:
                updated.append(item)
        raw["items"] = [item.to_dict() for item in updated]
        campaigns[index] = raw
        _save_campaigns(campaigns)
        return RetestCampaign(
            campaign_id=raw["campaign_id"],
            engagement_id=raw["engagement_id"],
            client_name=raw["client_name"],
            project_name=raw["project_name"],
            created_at=raw["created_at"],
            items=tuple(updated),
        )
    return None


def list_retest_campaigns(engagement_id: str | None = None) -> tuple[RetestCampaign, ...]:
    campaigns = []
    for raw in _load_campaigns():
        if engagement_id and raw.get("engagement_id") != engagement_id:
            continue
        items = tuple(RetestItem.from_dict(item) for item in raw.get("items", []))
        campaigns.append(
            RetestCampaign(
                campaign_id=raw["campaign_id"],
                engagement_id=raw["engagement_id"],
                client_name=raw.get("client_name", ""),
                project_name=raw.get("project_name", ""),
                created_at=raw.get("created_at", ""),
                items=items,
            )
        )
    return tuple(campaigns)


def retest_summary_markdown(campaign: RetestCampaign) -> str:
    verified = sum(1 for i in campaign.items if i.status == "verified")
    open_count = sum(1 for i in campaign.items if i.status == "open")
    lines = [
        "# Re-test & Validation Summary",
        "",
        f"**Campaign:** `{campaign.campaign_id}`",
        f"**Client:** {campaign.client_name}",
        f"**Project:** {campaign.project_name}",
        f"**Engagement:** `{campaign.engagement_id}`",
        "",
        f"**Verified:** {verified} / {len(campaign.items)} | **Open:** {open_count}",
        "",
        "| Finding | Severity | Status | Notes |",
        "| --- | --- | --- | --- |",
    ]
    for item in sorted(
        campaign.items,
        key=lambda i: SEVERITY_ORDER.index(i.original_severity.lower())
        if i.original_severity.lower() in SEVERITY_ORDER
        else 99,
    ):
        lines.append(
            f"| {item.finding_id} — {item.title} | {item.original_severity} | "
            f"{item.status} | {item.retest_notes or '—'} |"
        )
    return "\n".join(lines)


def export_retest_csv(campaign: RetestCampaign) -> str:
    lines = [
        "campaign_id,engagement_id,finding_id,title,original_severity,status,retest_notes,verified_at",
    ]
    for item in campaign.items:
        lines.append(
            f'"{campaign.campaign_id}","{campaign.engagement_id}","{item.finding_id}",'
            f'"{item.title}","{item.original_severity}","{item.status}",'
            f'"{item.retest_notes}","{item.verified_at or ""}"'
        )
    return "\n".join(lines) + "\n"