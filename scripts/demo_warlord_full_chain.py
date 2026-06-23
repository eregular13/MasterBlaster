#!/usr/bin/env python3
"""Savage demo: 12-MCP full assault chain — recon through evidence, 30+ tools."""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from masterblaster_control.mcp_tool_arsenal import (
    FULL_ASSAULT_CHAIN,
    WARLORD_TAGLINE,
    count_bound_tools,
    tools_for_mcp,
)
from masterblaster_control.runner_simulator import RunnerSimulator, build_default_engagement
from masterblaster_control.warlord_orchestrator import execute_warlord_chain, warlord_chain_markdown


def main() -> int:
    target = sys.argv[1] if len(sys.argv) > 1 else "example.com"
    tool_count = sum(len(tools_for_mcp(mcp_id)) for mcp_id in FULL_ASSAULT_CHAIN)
    print("=" * 72)
    print("  MASTERBLASTER WARLORD — FULL ASSAULT CHAIN")
    print(f"  {WARLORD_TAGLINE}")
    print("=" * 72)
    print(f"Target in crosshairs: {target}")
    print(f"Arsenal loaded: {count_bound_tools()} tools across 22 MCPs")
    print(f"Chain length: {len(FULL_ASSAULT_CHAIN)} MCPs · {tool_count} tools in this strike")
    print()

    runner = RunnerSimulator()
    engagement = build_default_engagement(target)
    result = execute_warlord_chain(runner, engagement, target, chain=FULL_ASSAULT_CHAIN)

    print(warlord_chain_markdown(result))
    print()
    print("JSON telemetry:")
    print(
        json.dumps(
            {
                "chain": "full",
                "target": result.target,
                "completed": result.completed,
                "denied": result.denied,
                "steps": [step.to_dict() for step in result.steps],
            },
            indent=2,
        )
    )
    print()
    print(f"Full whip cracked. {result.completed} strikes landed. Warlord standing by.")
    return 0 if result.completed >= len(FULL_ASSAULT_CHAIN) - 1 else 1


if __name__ == "__main__":
    raise SystemExit(main())