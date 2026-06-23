from datetime import datetime, timezone

from masterblaster_control.mcp_tool_arsenal import (
    DEFAULT_ASSAULT_CHAIN,
    FULL_ASSAULT_CHAIN,
    count_bound_tools,
)
from masterblaster_control.runner_simulator import RunnerSimulator, build_default_engagement
from masterblaster_control.warlord_orchestrator import (
    execute_warlord_chain,
    warlord_chain_json,
    warlord_chain_markdown,
)


def test_assault_chain_deploys_eight_mcps():
    assert len(DEFAULT_ASSAULT_CHAIN) >= 8


def test_full_assault_chain_deploys_twelve_mcps():
    assert len(FULL_ASSAULT_CHAIN) == 12


def test_warlord_chain_executes_with_evidence():
    now = datetime(2026, 6, 23, tzinfo=timezone.utc)
    runner = RunnerSimulator(signing_key=bytes(range(32)))
    engagement = build_default_engagement("example.com", now=now)
    result = execute_warlord_chain(runner, engagement, "example.com", now=now)
    assert len(result.steps) == len(DEFAULT_ASSAULT_CHAIN)
    assert result.completed >= 5
    assert all(step.tools for step in result.steps)


def test_full_warlord_chain_lands_majority_of_strikes():
    now = datetime(2026, 6, 23, tzinfo=timezone.utc)
    runner = RunnerSimulator(signing_key=bytes(range(32)))
    engagement = build_default_engagement("example.com", now=now)
    result = execute_warlord_chain(
        runner, engagement, "example.com", chain=FULL_ASSAULT_CHAIN, now=now
    )
    assert len(result.steps) == 12
    assert result.completed >= 10
    assert "Warlord Assault Chain Report" in warlord_chain_markdown(result)
    assert '"completed":' in warlord_chain_json(result)


def test_tool_arsenal_binds_dozens_of_tools():
    assert count_bound_tools() >= 60