from masterblaster_control.mcp_catalog import MCP_CATALOG_ORDER, build_mcp_catalog, catalog_markdown
from masterblaster_control.mcp_definitions import MCPS
from masterblaster_control.runner_simulator import MANIFESTS, MCP_COUNT, RunnerSimulator, build_default_engagement
from masterblaster_control.p0_approvals import approve_request, request_approval
from datetime import datetime, timezone


def test_catalog_registers_twenty_two_mcps():
    catalog = build_mcp_catalog()
    assert len(catalog) == 22
    assert len(MANIFESTS) == 22
    assert MCP_COUNT == 22
    assert len(MCPS) == 22
    assert tuple(catalog.keys()) == MCP_CATALOG_ORDER


def test_catalog_markdown_lists_all_slots():
    md = catalog_markdown()
    assert "22" in md
    for adapter_id in MCP_CATALOG_ORDER:
        assert adapter_id in md


def test_grokier_mcp_runs_through_runner_simulator():
    now = datetime(2026, 6, 23, tzinfo=timezone.utc)
    runner = RunnerSimulator(signing_key=bytes(range(32)))
    engagement = build_default_engagement("example.com", now=now)
    adapter_id = "mcp.recon.osint"
    approval = approve_request(
        request_approval(engagement, adapter_id, "example.com", now=now),
        now=now,
    )
    result = runner.run(adapter_id, "example.com", engagement=engagement, approval=approval, now=now)
    assert result.status == "completed"
    assert result.evidence[0].adapter_id == adapter_id