#!/usr/bin/env python3
"""Savage demo: deploy all 22 MCPs in catalog order — full registry queue."""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from masterblaster_control.mcp_tool_arsenal import FULL_REGISTRY_QUEUE, WARLORD_TAGLINE, count_bound_tools
from masterblaster_control.runner_simulator import RunnerSimulator, build_default_engagement
from masterblaster_control.warlord_orchestrator import (
    execute_registry_queue,
    registry_queue_markdown,
    warlord_chain_json,
)


def main() -> int:
    target = sys.argv[1] if len(sys.argv) > 1 else "example.com"
    print("=" * 72)
    print("  MASTERBLASTER WARLORD — 22-MCP REGISTRY QUEUE")
    print(f"  {WARLORD_TAGLINE}")
    print("=" * 72)
    print(f"Target in crosshairs: {target}")
    print(f"Arsenal loaded: {count_bound_tools()} tools across {len(FULL_REGISTRY_QUEUE)} MCPs")
    print()

    runner = RunnerSimulator()
    engagement = build_default_engagement(target)
    result = execute_registry_queue(runner, engagement, target)

    print(registry_queue_markdown(result))
    print()
    print("JSON telemetry:")
    print(warlord_chain_json(result, queue_type="registry"))
    print()
    print(f"Registry queue complete. {result.completed}/22 MCPs dominated.")
    return 0 if result.completed >= 20 else 1


if __name__ == "__main__":
    raise SystemExit(main())