from __future__ import annotations

from .runner_simulator import MANIFESTS

MCPS = [manifest.to_mcp_definition() for manifest in MANIFESTS.values()]


def get_mcp_by_id(adapter_id: str) -> dict | None:
    for mcp in MCPS:
        if mcp["id"] == adapter_id:
            return mcp
    return None
