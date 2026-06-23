from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

PLUGIN_SCHEMA_VERSION = "1.0"
REQUIRED_FIELDS = ("plugin_id", "name", "version", "min_core_version", "reviewed", "non_executing")


@dataclass(frozen=True)
class PluginManifest:
    plugin_id: str
    name: str
    version: str
    min_core_version: str
    reviewed: bool
    non_executing: bool
    description: str
    adapter_ids: tuple[str, ...]
    resource_uris: tuple[str, ...]
    source_path: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "plugin_id": self.plugin_id,
            "name": self.name,
            "version": self.version,
            "min_core_version": self.min_core_version,
            "reviewed": self.reviewed,
            "non_executing": self.non_executing,
            "description": self.description,
            "adapter_ids": list(self.adapter_ids),
            "resource_uris": list(self.resource_uris),
            "source_path": self.source_path,
        }


class PluginLoadError(ValueError):
    pass


def discover_plugins(plugins_root: str | Path | None = None) -> tuple[PluginManifest, ...]:
    root = Path(plugins_root or Path("plugins"))
    if not root.exists():
        return ()

    manifests: list[PluginManifest] = []
    for manifest_path in sorted(root.glob("*/plugin.json")):
        manifests.append(load_plugin_manifest(manifest_path))
    return tuple(manifests)


def load_plugin_manifest(path: str | Path) -> PluginManifest:
    manifest_path = Path(path)
    try:
        payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise PluginLoadError(f"{manifest_path} is not valid JSON") from exc

    if payload.get("schema_version") != PLUGIN_SCHEMA_VERSION:
        raise PluginLoadError(f"{manifest_path} schema_version must be {PLUGIN_SCHEMA_VERSION}")

    for field in REQUIRED_FIELDS:
        if field not in payload:
            raise PluginLoadError(f"{manifest_path} missing required field {field}")

    if not payload["reviewed"]:
        raise PluginLoadError(f"{manifest_path} plugin is not reviewed")
    if not payload["non_executing"]:
        raise PluginLoadError(f"{manifest_path} plugin must be non_executing in v1.0")

    return PluginManifest(
        plugin_id=str(payload["plugin_id"]),
        name=str(payload["name"]),
        version=str(payload["version"]),
        min_core_version=str(payload["min_core_version"]),
        reviewed=bool(payload["reviewed"]),
        non_executing=bool(payload["non_executing"]),
        description=str(payload.get("description", "")),
        adapter_ids=tuple(str(item) for item in payload.get("adapter_ids", [])),
        resource_uris=tuple(str(item) for item in payload.get("resource_uris", [])),
        source_path=str(manifest_path.parent),
    )


def plugin_catalog_markdown(plugins: tuple[PluginManifest, ...] | None = None) -> str:
    plugins = plugins if plugins is not None else discover_plugins()
    lines = [
        "# MasterBlaster Plugin Catalog",
        "",
        f"Discovered plugins: {len(plugins)}",
        "",
        "| Plugin | Version | Reviewed | Adapters | Resources |",
        "| --- | --- | --- | --- | --- |",
    ]
    for plugin in plugins:
        lines.append(
            f"| {plugin.name} | {plugin.version} | yes | "
            f"{len(plugin.adapter_ids)} | {len(plugin.resource_uris)} |"
        )
    if not plugins:
        lines.append("| _none_ | — | — | — | — |")
    return "\n".join(lines)