from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from .p7_plugins import PluginLoadError, PluginManifest, load_plugin_manifest

ReviewState = Literal["pending", "approved", "rejected"]


@dataclass(frozen=True)
class PluginReviewItem:
    plugin_id: str
    name: str
    version: str
    state: ReviewState
    submitter: str
    notes: str
    manifest_path: str

    def to_dict(self) -> dict[str, object]:
        return {
            "plugin_id": self.plugin_id,
            "name": self.name,
            "version": self.version,
            "state": self.state,
            "submitter": self.submitter,
            "notes": self.notes,
            "manifest_path": self.manifest_path,
        }


def discover_submissions(queue_root: str | Path | None = None) -> tuple[PluginReviewItem, ...]:
    root = Path(queue_root or Path("marketplace") / "submissions")
    if not root.exists():
        return ()

    items: list[PluginReviewItem] = []
    for manifest_path in sorted(root.glob("*/plugin.json")):
        try:
            manifest = load_plugin_manifest(manifest_path)
        except PluginLoadError:
            payload = json.loads(manifest_path.read_text(encoding="utf-8"))
            items.append(
                PluginReviewItem(
                    plugin_id=str(payload.get("plugin_id", manifest_path.parent.name)),
                    name=str(payload.get("name", "unknown")),
                    version=str(payload.get("version", "0.0.0")),
                    state="rejected",
                    submitter=str(payload.get("submitter", "unknown")),
                    notes="Manifest failed plugin loader validation.",
                    manifest_path=str(manifest_path),
                )
            )
            continue
        meta_path = manifest_path.parent / "submission.json"
        meta = json.loads(meta_path.read_text(encoding="utf-8")) if meta_path.exists() else {}
        items.append(
            PluginReviewItem(
                plugin_id=manifest.plugin_id,
                name=manifest.name,
                version=manifest.version,
                state=meta.get("state", "pending"),
                submitter=str(meta.get("submitter", "community")),
                notes=str(meta.get("notes", "")),
                manifest_path=str(manifest_path),
            )
        )
    return tuple(items)


def review_queue_markdown(queue_root: str | Path | None = None) -> str:
    items = discover_submissions(queue_root)
    lines = [
        "# Plugin Review Queue",
        "",
        f"Submissions: {len(items)}",
        "",
        "| Plugin | Version | State | Submitter | Notes |",
        "| --- | --- | --- | --- | --- |",
    ]
    for item in items:
        notes = item.notes or "—"
        lines.append(
            f"| {item.name} | {item.version} | {item.state} | {item.submitter} | {notes} |"
        )
    if not items:
        lines.append("| _none_ | — | — | — | Queue empty — see docs/community/PLUGIN_SUBMISSION.md |")
    return "\n".join(lines)


def summarize_manifest(manifest: PluginManifest) -> dict[str, object]:
    return {
        "plugin_id": manifest.plugin_id,
        "reviewed": manifest.reviewed,
        "non_executing": manifest.non_executing,
        "adapter_count": len(manifest.adapter_ids),
        "resource_count": len(manifest.resource_uris),
    }