#!/usr/bin/env python3
"""Read-only MCP-shaped stdio server for MasterBlaster P0 resources and draft tools."""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from masterblaster_control.p0_mcp_readonly import P0ReadOnlyMCPFacade, UnknownReadOnlyToolError
from masterblaster_control.p0_storage import P0Storage


def _respond(payload: dict) -> None:
    sys.stdout.write(json.dumps(payload) + "\n")
    sys.stdout.flush()


def handle_request(request: dict, facade: P0ReadOnlyMCPFacade) -> dict:
    method = request.get("method")
    if method == "list_resources":
        return {"resources": list(facade.list_resource_descriptors())}
    if method == "list_tools":
        return {"tools": list(facade.list_tool_descriptors())}
    if method == "read_resource":
        uri = request.get("uri", "")
        return {"resource": facade.read_resource(uri).to_dict()}
    if method == "call_tool":
        tool_name = request.get("tool", "")
        try:
            return {"result": facade.render_tool(tool_name).to_dict()}  # type: ignore[arg-type]
        except UnknownReadOnlyToolError as exc:
            return {"error": "unknown_tool", "message": str(exc), "readonly": True}
    if method == "ping":
        return {"pong": True, "readonly": True, "execution": False}
    return {"error": "unknown_method", "readonly": True}


def main() -> int:
    storage = P0Storage(":memory:")
    storage.initialize()
    facade = P0ReadOnlyMCPFacade(storage)

    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            request = json.loads(line)
        except json.JSONDecodeError:
            _respond({"error": "invalid_json"})
            continue
        _respond(handle_request(request, facade))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())