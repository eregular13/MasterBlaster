from masterblaster_control.mcp_catalog import MCP_CATALOG_ORDER
from masterblaster_control.mcp_tool_arsenal import MCP_TOOL_ARSENAL, tools_for_mcp


def test_every_mcp_has_tool_bindings():
    for adapter_id in MCP_CATALOG_ORDER:
        tools = tools_for_mcp(adapter_id)
        assert len(tools) >= 2
        assert adapter_id in MCP_TOOL_ARSENAL


def test_key_offensive_tools_are_mapped():
    all_tools = {tool for tools in MCP_TOOL_ARSENAL.values() for tool in tools}
    for expected in ("nmap", "sqlmap", "ffuf", "nuclei", "hydra", "burp", "metasploit"):
        assert expected in all_tools