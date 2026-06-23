from datetime import datetime, timezone

from masterblaster_control.mcp_tool_arsenal import (
    DEFAULT_ASSAULT_CHAIN,
    FULL_ASSAULT_CHAIN,
    FULL_REGISTRY_QUEUE,
    count_bound_tools,
)
from masterblaster_control.runner_simulator import RunnerSimulator, build_default_engagement
from masterblaster_control.warlord_orchestrator import (
    execute_registry_queue,
    execute_warlord_chain,
    execute_warlord_step,
    registry_queue_markdown,
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


def test_full_registry_queue_has_twenty_two_mcps():
    assert len(FULL_REGISTRY_QUEUE) == 22


def test_registry_queue_deploys_all_mcps():
    now = datetime(2026, 6, 23, tzinfo=timezone.utc)
    runner = RunnerSimulator(signing_key=bytes(range(32)))
    engagement = build_default_engagement("example.com", now=now)
    result = execute_registry_queue(runner, engagement, "example.com", now=now)
    assert len(result.steps) == 22
    assert result.completed >= 20
    assert "22 MCPs Under the Whip" in registry_queue_markdown(result)


def test_warlord_step_returns_runner_result():
    now = datetime(2026, 6, 23, tzinfo=timezone.utc)
    runner = RunnerSimulator(signing_key=bytes(range(32)))
    engagement = build_default_engagement("example.com", now=now)
    step, runner_result = execute_warlord_step(
        runner, engagement, "example.com", "a5.port.scan_sim", 1, now=now
    )
    assert step.status == "completed"
    assert runner_result is not None
    assert step.evidence_id