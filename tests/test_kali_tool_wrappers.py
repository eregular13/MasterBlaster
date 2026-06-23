from datetime import datetime, timezone

from masterblaster_control.kali_tool_wrappers import (
    KALI_TOOL_REGISTRY,
    build_command,
    get_tool,
    tool_arsenal_markdown,
    unleash_arsenal,
    unleash_tool,
)
from masterblaster_control.runner_simulator import RunnerSimulator, build_default_engagement


def test_registry_has_major_kali_tools():
    for tool_id in ("nmap", "nuclei", "sqlmap", "ffuf", "hydra", "metasploit", "burp"):
        assert tool_id in KALI_TOOL_REGISTRY


def test_build_command_substitutes_target():
    tool = get_tool("nmap")
    assert tool is not None
    command, preset = build_command(tool, "example.com", "syn-top")
    assert "example.com" in command
    assert "nmap" in command
    assert preset == "syn-top"


def test_unleash_tool_routes_through_mcp():
    now = datetime(2026, 6, 23, tzinfo=timezone.utc)
    runner = RunnerSimulator(signing_key=bytes(range(32)))
    engagement = build_default_engagement("example.com", now=now)
    result = unleash_tool(runner, engagement, "example.com", "nmap", preset_id="syn-top", now=now)
    assert result.status == "completed"
    assert result.mcp_adapter_id == "a5.port.scan_sim"
    assert result.evidence_id


def test_unleash_arsenal_batch():
    now = datetime(2026, 6, 23, tzinfo=timezone.utc)
    runner = RunnerSimulator(signing_key=bytes(range(32)))
    engagement = build_default_engagement("example.com", now=now)
    results = unleash_arsenal(
        runner, engagement, "example.com", tool_ids=("nmap", "nuclei", "sqlmap"), now=now
    )
    assert len(results) == 3
    assert sum(1 for r in results if r.status == "completed") >= 2


def test_tool_arsenal_markdown_renders():
    md = tool_arsenal_markdown()
    assert "Kali Tool Arsenal" in md
    assert "Nmap" in md