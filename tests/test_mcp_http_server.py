import json

from masterblaster_control.p0_mcp_readonly import P0ReadOnlyMCPFacade
from masterblaster_control.p0_storage import P0Storage
from scripts.mcp_http_server import handle_http_post, health_payload
from scripts.mcp_stdio_server import handle_request


def _facade() -> P0ReadOnlyMCPFacade:
    storage = P0Storage(":memory:")
    storage.initialize()
    return P0ReadOnlyMCPFacade(storage)


def test_mcp_http_health_payload():
    payload = health_payload()
    assert payload["status"] == "ok"
    assert payload["readonly"] is True


def test_mcp_http_post_delegates_to_handle_request():
    facade = _facade()
    status, payload = handle_http_post(json.dumps({"method": "ping"}).encode("utf-8"), facade)
    assert status == 200
    assert payload == handle_request({"method": "ping"}, facade)


def test_mcp_http_post_rejects_invalid_json():
    facade = _facade()
    status, payload = handle_http_post(b"{bad", facade)
    assert status == 400
    assert payload["error"] == "invalid_json"