#!/usr/bin/env python3
"""Read-only MCP-shaped HTTP server — JSON POST API over localhost only."""

from __future__ import annotations

import argparse
import json
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.mcp_stdio_server import handle_request
from masterblaster_control.p0_mcp_readonly import P0ReadOnlyMCPFacade
from masterblaster_control.p0_storage import P0Storage


class MCPHTTPHandler(BaseHTTPRequestHandler):
    facade: P0ReadOnlyMCPFacade

    def do_GET(self) -> None:
        if self.path != "/health":
            self._json_response(404, {"error": "not_found"})
            return
        self._json_response(200, health_payload())

    def do_POST(self) -> None:
        if self.path != "/mcp":
            self._json_response(404, {"error": "not_found"})
            return
        length = int(self.headers.get("Content-Length", "0"))
        body = self.rfile.read(length)
        status, payload = handle_http_post(body, self.facade)
        self._json_response(status, payload)

    def log_message(self, format: str, *args: object) -> None:
        return

    def _json_response(self, status: int, payload: dict) -> None:
        data = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)


def health_payload() -> dict[str, object]:
    return {"status": "ok", "readonly": True, "execution": False}


def handle_http_post(body: bytes, facade: P0ReadOnlyMCPFacade) -> tuple[int, dict]:
    try:
        request = json.loads(body.decode("utf-8"))
    except json.JSONDecodeError:
        return 400, {"error": "invalid_json"}
    return 200, handle_request(request, facade)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="MasterBlaster read-only MCP HTTP server")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args(argv)

    storage = P0Storage(":memory:")
    storage.initialize()
    MCPHTTPHandler.facade = P0ReadOnlyMCPFacade(storage)

    server = ThreadingHTTPServer((args.host, args.port), MCPHTTPHandler)
    print(f"MCP HTTP server listening on http://{args.host}:{args.port} (readonly)", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    return 0


if __name__ == "__main__":
    raise SystemExit(main())