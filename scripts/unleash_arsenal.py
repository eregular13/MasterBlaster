#!/usr/bin/env python3
"""CLI: unleash Kali-grade tools through governed MCP wrappers."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from masterblaster_control.kali_tool_wrappers import (
    KALI_TOOL_REGISTRY,
    list_tools,
    tool_arsenal_markdown,
    unleash_arsenal,
    unleash_tool,
)
from masterblaster_control.runner_simulator import RunnerSimulator, build_default_engagement


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="MasterBlaster WARLORD — unleash Kali tools through MCP governors"
    )
    parser.add_argument("target", nargs="?", default="example.com", help="Authorized target")
    parser.add_argument("--tool", "-t", action="append", help="Tool ID (repeatable)")
    parser.add_argument("--preset", "-p", help="Preset ID for single tool unleash")
    parser.add_argument("--category", "-c", help="Unleash all tools in category")
    parser.add_argument("--all", action="store_true", help="Unleash entire arsenal")
    parser.add_argument("--list", action="store_true", help="List available tools")
    parser.add_argument("--markdown", action="store_true", help="Print arsenal markdown table")
    return parser


def main() -> int:
    args = build_parser().parse_args()

    if args.markdown:
        print(tool_arsenal_markdown())
        return 0

    if args.list:
        for tool in list_tools(category=args.category):
            presets = ", ".join(p.preset_id for p in tool.presets)
            print(f"{tool.tool_id:14} {tool.category:8} mcp={tool.mcp_adapter_id} presets=[{presets}]")
        return 0

    runner = RunnerSimulator()
    engagement = build_default_engagement(args.target)

    if args.all:
        tool_ids = tuple(KALI_TOOL_REGISTRY.keys())
        results = unleash_arsenal(runner, engagement, args.target, tool_ids=tool_ids)
    elif args.category:
        tool_ids = tuple(t.tool_id for t in list_tools(category=args.category))
        results = unleash_arsenal(runner, engagement, args.target, tool_ids=tool_ids)
    elif args.tool:
        if len(args.tool) == 1:
            results = (unleash_tool(runner, engagement, args.target, args.tool[0], preset_id=args.preset),)
        else:
            results = unleash_arsenal(runner, engagement, args.target, tool_ids=tuple(args.tool))
    else:
        print("Specify --tool, --category, --all, --list, or --markdown", file=sys.stderr)
        return 2

    completed = sum(1 for r in results if r.status == "completed")
    print(json.dumps({"target": args.target, "completed": completed, "total": len(results), "strikes": [r.to_dict() for r in results]}, indent=2))
    print(f"\nArsenal unleashed: {completed}/{len(results)} tools commanded.")
    return 0 if completed > 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())