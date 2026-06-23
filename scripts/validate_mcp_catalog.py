#!/usr/bin/env python3
"""Validate the 22-MCP Grokier catalog."""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from masterblaster_control.mcp_catalog import MCP_CATALOG_ORDER, build_mcp_catalog, catalog_markdown
from masterblaster_control.mcp_definitions import MCPS
from masterblaster_control.runner_simulator import MANIFESTS


def main() -> int:
    print("=== Validate 22-MCP Catalog ===")
    catalog = build_mcp_catalog()
    if len(catalog) != 22:
        print(f"ERROR: expected 22 MCPs, found {len(catalog)}", file=sys.stderr)
        return 1
    if len(MCPS) != 22:
        print(f"ERROR: MCPS export has {len(MCPS)} entries", file=sys.stderr)
        return 1
    for adapter_id in MCP_CATALOG_ORDER:
        manifest = MANIFESTS.get(adapter_id)
        if manifest is None or not manifest.reviewed:
            print(f"ERROR: missing or unreviewed {adapter_id}", file=sys.stderr)
            return 1
        print(f"OK {adapter_id} tier={manifest.tier} mode={manifest.execution_mode}")
    print(catalog_markdown())
    print("Validated 22 MCP catalog entries.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())