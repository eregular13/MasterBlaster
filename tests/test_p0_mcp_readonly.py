import inspect

import pytest

from masterblaster_control import p0_mcp_readonly
from masterblaster_control.p0_mcp_readonly import P0ReadOnlyMCPFacade, UnknownReadOnlyToolError
from masterblaster_control.p0_storage import P0Storage


def test_readonly_facade_lists_resources_and_tools_without_execution_surface():
    facade = P0ReadOnlyMCPFacade(P0Storage(":memory:"))

    resources = facade.list_resource_descriptors()
    tools = facade.list_tool_descriptors()

    assert len(resources) >= 5
    assert all(resource["non_executing"] is True for resource in resources)
    assert [tool["name"] for tool in tools] == ["planning_brief", "report_draft"]
    assert all(tool["non_executing"] is True for tool in tools)
    assert all("run" not in tool["name"] for tool in tools)


def test_readonly_facade_reads_registered_resource():
    facade = P0ReadOnlyMCPFacade(P0Storage(":memory:"))

    resource = facade.read_resource("p0://governance/acceptance-checklist")

    assert resource.non_executing is True
    assert "P0 Acceptance Dashboard" in resource.body


def test_readonly_facade_fails_closed_for_unknown_tool():
    facade = P0ReadOnlyMCPFacade(P0Storage(":memory:"))

    with pytest.raises(UnknownReadOnlyToolError):
        facade.render_tool("runner_job")  # type: ignore[arg-type]


def test_planning_brief_is_non_executing_markdown():
    facade = P0ReadOnlyMCPFacade(P0Storage(":memory:"))

    result = facade.render_tool("planning_brief")

    assert result.non_executing is True
    assert result.content_type == "text/markdown"
    assert "cannot execute jobs" in result.body
    assert "Non-Executing P0 Resources" in result.body


def test_report_draft_is_non_certifying_and_uses_storage_snapshot():
    facade = P0ReadOnlyMCPFacade(P0Storage(":memory:"))

    result = facade.render_tool("report_draft")

    assert result.non_executing is True
    assert "simulator draft only" in result.body
    assert "Tenants: 0" in result.body
    assert "P1 gate" in result.body


def test_readonly_facade_does_not_import_runner_simulator():
    source = inspect.getsource(p0_mcp_readonly)

    assert "RunnerSimulator" not in source
    assert "runner_simulator" not in source
