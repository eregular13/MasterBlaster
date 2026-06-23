from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

FeatureName = Literal[
    "a7_live_adapter",
    "oidc_auth",
    "hsm_signing",
    "mcp_http",
    "plugin_marketplace",
    "codesigned_installer",
]


@dataclass(frozen=True)
class FeatureFlag:
    name: FeatureName
    enabled: bool
    description: str

    def to_dict(self) -> dict[str, object]:
        return {"name": self.name, "enabled": self.enabled, "description": self.description}


_DEFAULTS: dict[FeatureName, tuple[bool, str]] = {
    "a7_live_adapter": (False, "A7 live transport adapter — blocked unless explicitly enabled."),
    "oidc_auth": (False, "OIDC auth provider skeleton — no network calls in v1.0."),
    "hsm_signing": (False, "External HSM key store delegation — local file/env only."),
    "mcp_http": (True, "Read-only MCP HTTP wrapper for integrations."),
    "plugin_marketplace": (False, "Community plugin marketplace catalog — manifest review only."),
    "codesigned_installer": (False, "Authenticode signing — requires Windows cert in CI."),
}


def _env_override(name: FeatureName) -> bool | None:
    key = f"MB_FEATURE_{name.upper()}"
    raw = os.environ.get(key)
    if raw is None:
        return None
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def load_feature_flags(path: str | Path | None = None) -> tuple[FeatureFlag, ...]:
    config_path = Path(path or Path("data") / "feature_flags.json")
    file_overrides: dict[str, bool] = {}
    if config_path.exists():
        payload = json.loads(config_path.read_text(encoding="utf-8"))
        file_overrides = {str(k): bool(v) for k, v in payload.get("flags", {}).items()}

    flags: list[FeatureFlag] = []
    for name, (default_enabled, description) in _DEFAULTS.items():
        enabled = default_enabled
        if name in file_overrides:
            enabled = file_overrides[name]
        env_value = _env_override(name)
        if env_value is not None:
            enabled = env_value
        flags.append(FeatureFlag(name=name, enabled=enabled, description=description))
    return tuple(flags)


def is_feature_enabled(name: FeatureName, path: str | Path | None = None) -> bool:
    return next(flag.enabled for flag in load_feature_flags(path) if flag.name == name)


def feature_flags_markdown(path: str | Path | None = None) -> str:
    lines = [
        "# MasterBlaster Feature Flags",
        "",
        "| Flag | Enabled | Description |",
        "| --- | ---: | --- |",
    ]
    for flag in load_feature_flags(path):
        lines.append(f"| `{flag.name}` | {'yes' if flag.enabled else 'no'} | {flag.description} |")
    return "\n".join(lines)