import json
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path


def test_mcp_http_health_endpoint():
    script = Path(__file__).resolve().parents[1] / "scripts" / "mcp_http_server.py"
    proc = subprocess.Popen(
        [sys.executable, str(script), "--port", "18765"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    try:
        for _ in range(30):
            try:
                with urllib.request.urlopen("http://127.0.0.1:18765/health", timeout=1) as resp:
                    payload = json.loads(resp.read().decode("utf-8"))
                assert payload["status"] == "ok"
                assert payload["readonly"] is True
                return
            except urllib.error.URLError:
                pass
        raise AssertionError("MCP HTTP server did not become ready")
    finally:
        proc.terminate()
        proc.wait(timeout=5)