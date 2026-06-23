from scripts.mcp_stdio_server import handle_request
from masterblaster_control.p0_mcp_readonly import P0ReadOnlyMCPFacade
from masterblaster_control.p0_storage import P0Storage


def _facade() -> P0ReadOnlyMCPFacade:
    storage = P0Storage(":memory:")
    storage.initialize()
    return P0ReadOnlyMCPFacade(storage)


def test_handle_request_lists_resources_and_tools():
    facade = _facade()

    resources = handle_request({"method": "list_resources"}, facade)
    tools = handle_request({"method": "list_tools"}, facade)

    assert len(resources["resources"]) >= 5
    assert [tool["name"] for tool in tools["tools"]] == ["planning_brief", "report_draft"]


def test_handle_request_reads_resource_and_renders_tool():
    facade = _facade()

    resource = handle_request({"method": "read_resource", "uri": "p0://governance/acceptance-checklist"}, facade)
    result = handle_request({"method": "call_tool", "tool": "planning_brief"}, facade)

    assert "P0 Acceptance Dashboard" in resource["resource"]["body"]
    assert result["result"]["non_executing"] is True
    assert "cannot execute jobs" in result["result"]["body"]


def test_handle_request_fails_closed_for_unknown_tool():
    facade = _facade()

    response = handle_request({"method": "call_tool", "tool": "runner_job"}, facade)

    assert response["error"] == "unknown_tool"
    assert response["readonly"] is True


def test_handle_request_ping():
    facade = _facade()
    payload = handle_request({"method": "ping"}, facade)
    assert payload["pong"] is True
    assert payload["readonly"] is True