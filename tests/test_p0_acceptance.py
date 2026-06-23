import pytest

from masterblaster_control.p0_acceptance import (
    UnknownAcceptanceCriterionError,
    acceptance_dashboard_markdown,
    acceptance_summary,
    list_acceptance_criteria,
    read_acceptance_criterion,
)


def test_acceptance_criteria_are_frozen_and_bounded():
    criteria = list_acceptance_criteria()

    assert len(criteria) >= 20
    assert all(0 <= criterion.percent <= 100 for criterion in criteria)
    assert all(criterion.evidence for criterion in criteria)
    assert all(criterion.next_action for criterion in criteria)


def test_acceptance_summary_is_stable_and_has_p1_blockers():
    summary = acceptance_summary()

    assert summary.total == len(list_acceptance_criteria())
    assert summary.complete >= 13
    assert summary.partial >= 3
    assert summary.not_started >= 4
    assert 60 <= summary.overall_percent <= 90
    assert 60 <= summary.p1_gate_percent <= 90
    assert "approvals.human_gate" in summary.p1_blockers
    assert "mcp.read_only_wrapper" in summary.p1_blockers


def test_acceptance_lookup_fails_closed_for_unknown_ids():
    with pytest.raises(UnknownAcceptanceCriterionError):
        read_acceptance_criterion("execution.live_tool_escape_hatch")


def test_acceptance_dashboard_markdown_contains_evidence_and_next_actions():
    dashboard = acceptance_dashboard_markdown()

    assert dashboard.startswith("# P0 Acceptance Dashboard")
    assert "Overall reference completion" in dashboard
    assert "P1 gate completion" in dashboard
    assert "Runner-side validation independent of UI" in dashboard
    assert "Human approval state machine" in dashboard
    assert "| Criterion | Status | % | P1 Gate | Evidence | Next Action |" in dashboard
