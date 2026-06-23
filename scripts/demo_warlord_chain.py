#!/usr/bin/env python3
"""Savage demo: crack the whip across 8 MCPs with Kali-grade tool bindings."""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from masterblaster_control.mcp_tool_arsenal import (
    DEFAULT_ASSAULT_CHAIN,
    WARLORD_TAGLINE,
    arsenal_markdown,
    count_bound_tools,
)
from masterblaster_control.runner_simulator import RunnerSimulator, build_default_engagement
from masterblaster_control.warlord_orchestrator import execute_warlord_chain, warlord_chain_markdown


def main() -> int:
    target = sys.argv[1] if len(sys.argv) > 1 else "example.com"
    print("=" * 72)
    print("  MASTERBLASTER WARLORD — ASSAULT CHAIN DEMO")
    print(f"  {WARLORD_TAGLINE}")
    print("=" * 72)
    print(f"Target in crosshairs: {target}")
    print(f"Tool bindings loaded: {count_bound_tools()} across 22 MCPs")
    print(f"Chain length: {len(DEFAULT_ASSAULT_CHAIN)} MCPs")
    print()

    runner = RunnerSimulator()
    engagement = build_default_engagement(target)
    result = execute_warlord_chain(runner, engagement, target)

    print(warlord_chain_markdown(result))
    print()
    print("JSON telemetry:")
    print(
        json.dumps(
            {
                "target": result.target,
                "completed": result.completed,
                "denied": result.denied,
                "steps": [step.to_dict() for step in result.steps],
            },
            indent=2,
        )
    )
    print()
    print("Arsenal snapshot:")
    print(arsenal_markdown())
    print()
    print("Whip cracked. Evidence captured. Warlord standing by.")
    return 0 if result.completed > 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())