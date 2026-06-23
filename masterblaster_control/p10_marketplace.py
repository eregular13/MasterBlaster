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


@dataclass(frozen=True)
class WarPack:
    pack_id: str
    name: str
    version: str
    author: str
    reviewed: bool
    description: str
    mcp_chain: tuple[str, ...]
    tools: tuple[str, ...]
    special: str | None = None

    def to_dict(self) -> dict[str, object]:
        return {
            "pack_id": self.pack_id,
            "name": self.name,
            "version": self.version,
            "author": self.author,
            "reviewed": self.reviewed,
            "description": self.description,
            "mcp_chain": list(self.mcp_chain),
            "tools": list(self.tools),
            "special": self.special,
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


def load_war_packs(path: str | Path | None = None) -> tuple[WarPack, ...]:
    packs_path = Path(path or Path("marketplace") / "war_packs.json")
    if not packs_path.exists():
        return ()
    payload = json.loads(packs_path.read_text(encoding="utf-8"))
    return tuple(
        WarPack(
            pack_id=str(item["pack_id"]),
            name=str(item["name"]),
            version=str(item["version"]),
            author=str(item.get("author", "community")),
            reviewed=bool(item.get("reviewed", False)),
            description=str(item.get("description", "")),
            mcp_chain=tuple(str(m) for m in item.get("mcp_chain", [])),
            tools=tuple(str(t) for t in item.get("tools", [])),
            special=str(item["special"]) if item.get("special") else None,
        )
        for item in payload.get("war_packs", [])
    )


def marketplace_markdown(path: str | Path | None = None) -> str:
    enabled = is_feature_enabled("plugin_marketplace")
    listings = load_marketplace_catalog(path)
    war_packs = load_war_packs()
    lines = [
        "# MasterBlaster Warlord Marketplace",
        "",
        f"- Feature enabled: **{'yes' if enabled else 'no'}**",
        f"- Plugin listings: {len(listings)}",
        f"- **War Packs:** {len(war_packs)}",
        "",
        "## War Packs — Pre-Configured Toolchains",
        "",
        "| Pack | MCPs | Tools | Reviewed | Author |",
        "| --- | ---: | ---: | ---: | --- |",
    ]
    for pack in war_packs:
        mcp_count = "22 (full)" if pack.special == "full_registry_queue" else str(len(pack.mcp_chain))
        tool_count = "all" if pack.special == "full_registry_queue" else str(len(pack.tools))
        reviewed = "yes" if pack.reviewed else "no"
        lines.append(
            f"| **{pack.name}** | {mcp_count} | {tool_count} | {reviewed} | {pack.author} |"
        )
        lines.append(f"| _{pack.description}_ | | | | |")
    lines.extend(
        [
            "",
            "## Plugin Listings",
            "",
            "| Listing | Plugin | Version | Reviewed | Author |",
            "| --- | --- | --- | ---: | --- |",
        ]
    )
    for entry in listings:
        reviewed = "yes" if entry.reviewed else "no"
        lines.append(
            f"| {entry.listing_id} | {entry.name} | {entry.version} | {reviewed} | {entry.author} |"
        )
    if not listings:
        lines.append("| _none_ | — | — | — | Submit via docs/community/PLUGIN_SUBMISSION.md |")
    return "\n".join(lines)


def war_packs_markdown(path: str | Path | None = None) -> str:
    packs = load_war_packs(path)
    lines = [
        "# MasterBlaster War Packs",
        "",
        "> Pre-configured MCP + tool chains. Load a pack. Crack the whip.",
        "",
        f"**Available packs:** {len(packs)}",
        "",
    ]
    for pack in packs:
        reviewed = "REVIEWED" if pack.reviewed else "PENDING REVIEW"
        lines.append(f"## {pack.name} (`{pack.pack_id}`) — {reviewed}")
        lines.append(f"_{pack.description}_")
        if pack.special == "full_registry_queue":
            lines.append("- **Mode:** Full 22-MCP registry queue + entire arsenal")
        else:
            if pack.mcp_chain:
                lines.append(f"- **MCP chain:** {', '.join(f'`{m}`' for m in pack.mcp_chain)}")
            if pack.tools:
                lines.append(f"- **Tools:** {', '.join(f'`{t}`' for t in pack.tools)}")
        lines.append("")
    return "\n".join(lines)