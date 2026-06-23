from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from .p9_feature_flags import is_feature_enabled


@dataclass(frozen=True)
class MarketplaceEntry:
    listing_id: str
    plugin_id: str
    name: str
    version: str
    author: str
    reviewed: bool
    description: str

    def to_dict(self) -> dict[str, object]:
        return {
            "listing_id": self.listing_id,
            "plugin_id": self.plugin_id,
            "name": self.name,
            "version": self.version,
            "author": self.author,
            "reviewed": self.reviewed,
            "description": self.description,
        }


def load_marketplace_catalog(path: str | Path | None = None) -> tuple[MarketplaceEntry, ...]:
    catalog_path = Path(path or Path("marketplace") / "catalog.json")
    if not catalog_path.exists():
        return ()
    payload = json.loads(catalog_path.read_text(encoding="utf-8"))
    return tuple(
        MarketplaceEntry(
            listing_id=str(item["listing_id"]),
            plugin_id=str(item["plugin_id"]),
            name=str(item["name"]),
            version=str(item["version"]),
            author=str(item.get("author", "community")),
            reviewed=bool(item.get("reviewed", False)),
            description=str(item.get("description", "")),
        )
        for item in payload.get("listings", [])
    )


def marketplace_markdown(path: str | Path | None = None) -> str:
    enabled = is_feature_enabled("plugin_marketplace")
    listings = load_marketplace_catalog(path)
    lines = [
        "# MasterBlaster Plugin Marketplace (Skeleton)",
        "",
        f"- Feature enabled: **{'yes' if enabled else 'no'}**",
        f"- Listings: {len(listings)}",
        "",
        "| Listing | Plugin | Version | Reviewed | Author |",
        "| --- | --- | --- | ---: | --- |",
    ]
    for entry in listings:
        reviewed = "yes" if entry.reviewed else "no"
        lines.append(
            f"| {entry.listing_id} | {entry.name} | {entry.version} | {reviewed} | {entry.author} |"
        )
    if not listings:
        lines.append("| _none_ | — | — | — | Submit via docs/community/PLUGIN_SUBMISSION.md |")
    return "\n".join(lines)