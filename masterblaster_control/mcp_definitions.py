from __future__ import annotations

from .mcp_catalog import MCP_CATALOG_ORDER
from .runner_simulator import MANIFESTS

MCPS = [MANIFESTS[adapter_id].to_mcp_definition() for adapter_id in MCP_CATALOG_ORDER]


def get_mcp_by_id(adapter_id: str) -> dict | None:
    for mcp in MCPS:
        if mcp["id"] == adapter_id:
            return mcp
    return None
