import pytest

from masterblaster_control.p0_acceptance import (
    UnknownAcceptanceCriterionError,
    acceptance_dashboard_json,
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
    assert all(criterion.verifier_ids for criterion in criteria)
    assert all(criterion.next_action for criterion in criteria)


def test_acceptance_summary_is_stable_and_has_p1_blockers():
    summary = acceptance_summary()

    assert summary.total == len(list_acceptance_criteria())
    assert summary.complete >= 18
    assert summary.partial == 2
    assert 80 <= summary.overall_percent <= 100
    assert 80 <= summary.p1_gate_percent < 100
    assert "approvals.human_gate" not in summary.p1_blockers
    assert "storage.retention_redaction" not in summary.p1_blockers
    assert "mcp.read_only_wrapper" not in summary.p1_blockers
    assert "ci.sbom_drift" not in summary.p1_blockers
    assert "ci.github_dependency_review" in summary.p1_blockers
    assert "governance.review_policy_artifacts" not in summary.p1_blockers
    assert "governance.remote_enforcement" in summary.p1_blockers
    assert set(summary.p1_blockers) == {"ci.github_dependency_review", "governance.remote_enforcement"}


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
    assert "| Criterion | Status | % | P1 Gate | Evidence | Failed Verifiers | Next Action |" in dashboard
    assert "external.dependency_graph.verified" in dashboard


def test_acceptance_dashboard_json_contains_failed_verifier_reasons():
    dashboard = acceptance_dashboard_json()

    assert '"p1_blockers"' in dashboard
    assert "ci.github_dependency_review" in dashboard
    assert "external.remote_review_enforcement.verified" in dashboard
