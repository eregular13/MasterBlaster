from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Literal

AcceptanceCategory = Literal["security", "execution", "evidence", "governance", "ux", "operations"]
AcceptanceStatus = Literal["complete", "partial", "not_started"]


class UnknownAcceptanceCriterionError(KeyError):
    pass


@dataclass(frozen=True)
class AcceptanceCriterion:
    criterion_id: str
    title: str
    category: AcceptanceCategory
    status: AcceptanceStatus
    percent: int
    required_for_p1: bool
    evidence: tuple[str, ...]
    next_action: str

    def __post_init__(self) -> None:
        if not 0 <= self.percent <= 100:
            raise ValueError(f"{self.criterion_id} percent must be between 0 and 100")

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class AcceptanceSummary:
    total: int
    complete: int
    partial: int
    not_started: int
    overall_percent: int
    p1_gate_percent: int
    p1_blockers: tuple[str, ...]


_CRITERIA: tuple[AcceptanceCriterion, ...] = (
    AcceptanceCriterion(
        criterion_id="manifest.reviewed_registry",
        title="Reviewed adapter manifest registry",
        category="security",
        status="complete",
        percent=100,
        required_for_p1=True,
        evidence=("masterblaster_control/runner_simulator.py", "tests/test_runner_simulator.py"),
        next_action="Add manifest signing metadata before live adapters exist.",
    ),
    AcceptanceCriterion(
        criterion_id="policy.scope_validation",
        title="Deterministic target parsing and scope decisions",
        category="security",
        status="complete",
        percent=100,
        required_for_p1=True,
        evidence=("masterblaster_control/p0_policy.py", "tests/test_p0_policy.py"),
        next_action="Add property-style target corpus tests.",
    ),
    AcceptanceCriterion(
        criterion_id="policy.reason_codes",
        title="Stable policy reason codes",
        category="security",
        status="complete",
        percent=100,
        required_for_p1=True,
        evidence=("masterblaster_control/p0_policy.py",),
        next_action="Document reason-code contract in API docs.",
    ),
    AcceptanceCriterion(
        criterion_id="jobs.signed_expiring_envelopes",
        title="Signed, expiring, bound job envelopes",
        category="execution",
        status="complete",
        percent=100,
        required_for_p1=True,
        evidence=("masterblaster_control/p0_models.py", "masterblaster_control/p0_policy.py"),
        next_action="Add key-rotation design note.",
    ),
    AcceptanceCriterion(
        criterion_id="runner.independent_validation",
        title="Runner-side validation independent of UI",
        category="execution",
        status="complete",
        percent=100,
        required_for_p1=True,
        evidence=("masterblaster_control/runner_simulator.py", "tests/test_runner_simulator.py"),
        next_action="Add runner request/response contract docs.",
    ),
    AcceptanceCriterion(
        criterion_id="adapters.a0_fixture_inventory",
        title="Offline A0 fixture inventory adapter",
        category="execution",
        status="complete",
        percent=100,
        required_for_p1=True,
        evidence=("masterblaster_control/runner_simulator.py",),
        next_action="Move fixture payloads to versioned fixture files.",
    ),
    AcceptanceCriterion(
        criterion_id="adapters.a1_tls_fake_transport",
        title="A1 TLS assessment behind fake transport",
        category="execution",
        status="complete",
        percent=100,
        required_for_p1=True,
        evidence=("masterblaster_control/runner_simulator.py", "tests/test_runner_simulator.py"),
        next_action="Add alternate TLS fixture scenarios.",
    ),
    AcceptanceCriterion(
        criterion_id="evidence.hashing_provenance",
        title="Deterministic evidence hashes and parser provenance",
        category="evidence",
        status="complete",
        percent=100,
        required_for_p1=True,
        evidence=("masterblaster_control/p0_models.py", "tests/test_runner_simulator.py"),
        next_action="Add finding/mapping projection from evidence.",
    ),
    AcceptanceCriterion(
        criterion_id="storage.local_audit",
        title="Persistent local audit for completed and denied outcomes",
        category="evidence",
        status="complete",
        percent=100,
        required_for_p1=True,
        evidence=(
            "masterblaster_control/p0_storage.py",
            "masterblaster_control/p0_approvals.py",
            "masterblaster_control/p0_retention.py",
            "tests/test_p0_storage.py",
        ),
        next_action="Add operator-configurable retention presets in the Qt settings panel.",
    ),
    AcceptanceCriterion(
        criterion_id="resources.non_executing_registry",
        title="Non-executing planning, reporting, governance resources",
        category="governance",
        status="complete",
        percent=100,
        required_for_p1=True,
        evidence=("masterblaster_control/p0_resources.py", "tests/test_p0_resources.py"),
        next_action="Keep resource records transport-agnostic as the MCP facade evolves.",
    ),
    AcceptanceCriterion(
        criterion_id="testing.negative_first",
        title="Negative tests for deny-by-default policy behavior",
        category="operations",
        status="complete",
        percent=100,
        required_for_p1=True,
        evidence=("tests/test_p0_policy.py",),
        next_action="Add mutation-style tests for policy bypass attempts.",
    ),
    AcceptanceCriterion(
        criterion_id="docs.security_threat_model",
        title="Security impact and threat-model impact documentation",
        category="governance",
        status="complete",
        percent=100,
        required_for_p1=True,
        evidence=("docs/SECURITY_IMPACT.md", "docs/THREAT_MODEL_IMPACT.md"),
        next_action="Add formal data-flow diagram doc.",
    ),
    AcceptanceCriterion(
        criterion_id="reports.draft_disclaimer",
        title="Report drafts disclaim compliance certification",
        category="governance",
        status="complete",
        percent=100,
        required_for_p1=True,
        evidence=("README.md", "ethics.md", "masterblaster_control/utils.py"),
        next_action="Add report template snapshot tests.",
    ),
    AcceptanceCriterion(
        criterion_id="governance.acceptance_dashboard",
        title="Machine-readable acceptance dashboard",
        category="governance",
        status="complete",
        percent=100,
        required_for_p1=True,
        evidence=("masterblaster_control/p0_acceptance.py", "tests/test_p0_acceptance.py"),
        next_action="Link dashboard rows to persisted evidence IDs.",
    ),
    AcceptanceCriterion(
        criterion_id="approvals.human_gate",
        title="Human approval state machine for simulator requests",
        category="security",
        status="complete",
        percent=100,
        required_for_p1=True,
        evidence=(
            "masterblaster_control/p0_approvals.py",
            "masterblaster_control/runner_simulator.py",
            "masterblaster_control/mcp_tab.py",
            "tests/test_p0_approvals.py",
        ),
        next_action="Add multi-approver and approval-policy configuration for future production use.",
    ),
    AcceptanceCriterion(
        criterion_id="ui.tenant_engagement_management",
        title="Tenant/client/engagement management UI over storage",
        category="ux",
        status="complete",
        percent=100,
        required_for_p1=False,
        evidence=(
            "masterblaster_control/p0_storage.py",
            "masterblaster_control/storage_browser.py",
            "tests/test_p0_storage_crud.py",
        ),
        next_action="Add edit/delete flows and engagement picker in simulator tabs.",
    ),
    AcceptanceCriterion(
        criterion_id="mcp.read_only_wrapper",
        title="MCP read-only wrapper for resources and draft tools",
        category="operations",
        status="complete",
        percent=100,
        required_for_p1=True,
        evidence=(
            "masterblaster_control/p0_mcp_readonly.py",
            "tests/test_p0_mcp_readonly.py",
            "docs/architecture/p0-readonly-mcp.md",
        ),
        next_action="Wrap the facade with an actual MCP transport after CI and review policy land.",
    ),
    AcceptanceCriterion(
        criterion_id="adapters.additional_fixtures",
        title="Additional fixture adapters and parser scenarios",
        category="execution",
        status="complete",
        percent=100,
        required_for_p1=False,
        evidence=("masterblaster_control/runner_simulator.py", "tests/test_runner_simulator.py"),
        next_action="Move fixture payloads into versioned files per adapter tier.",
    ),
    AcceptanceCriterion(
        criterion_id="ci.sbom_dependency_review",
        title="CI workflow for tests, dependency review, and SBOM stubs",
        category="operations",
        status="complete",
        percent=100,
        required_for_p1=True,
        evidence=(
            ".github/workflows/p0-verification.yml",
            ".github/workflows/p0-ci.yml",
            ".github/workflows/dependency-review.yml",
            "scripts/generate_sbom.py",
            "scripts/generate_sbom_stub.py",
            "sbom/masterblaster-p0.spdx.json",
            "tests/test_sbom_generation.py",
            "tests/test_p0_ci.py",
            "docs/supply-chain/sbom-and-dependency-review.md",
        ),
        next_action="Enable dependency graph and required workflow checks in GitHub repository settings.",
    ),
    AcceptanceCriterion(
        criterion_id="governance.review_policy",
        title="Review policy for security-sensitive files",
        category="governance",
        status="complete",
        percent=100,
        required_for_p1=True,
        evidence=(
            ".github/CODEOWNERS",
            ".github/pull_request_template.md",
            "policy/security-sensitive-paths.json",
            "scripts/validate_governance.py",
            "tests/test_governance_review_policy.py",
            "docs/governance/security-review-policy.md",
            "docs/REVIEW_POLICY.md",
        ),
        next_action="Enable CODEOWNERS-required review and branch protection in GitHub repository settings.",
    ),
    AcceptanceCriterion(
        criterion_id="storage.retention_redaction",
        title="Storage retention and redaction policy",
        category="security",
        status="complete",
        percent=100,
        required_for_p1=True,
        evidence=(
            "masterblaster_control/p0_retention.py",
            "masterblaster_control/p0_storage.py",
            "tests/test_p0_retention.py",
            "tests/test_p0_storage.py",
        ),
        next_action="Add per-engagement retention overrides after management UI exists.",
    ),
    AcceptanceCriterion(
        criterion_id="ui.audit_browser",
        title="Rich audit and evidence browser in Qt UI",
        category="ux",
        status="complete",
        percent=100,
        required_for_p1=False,
        evidence=(
            "masterblaster_control/main_window.py",
            "masterblaster_control/storage_browser.py",
            "tests/test_p0_storage_crud.py",
        ),
        next_action="Add paginated history and cross-engagement comparison views.",
    ),
)

_CRITERION_BY_ID = {criterion.criterion_id: criterion for criterion in _CRITERIA}


def list_acceptance_criteria() -> tuple[AcceptanceCriterion, ...]:
    return _CRITERIA


def read_acceptance_criterion(criterion_id: str) -> AcceptanceCriterion:
    try:
        return _CRITERION_BY_ID[criterion_id]
    except KeyError as exc:
        raise UnknownAcceptanceCriterionError(f"Unknown acceptance criterion: {criterion_id}") from exc


def acceptance_summary() -> AcceptanceSummary:
    total = len(_CRITERIA)
    complete = sum(1 for criterion in _CRITERIA if criterion.status == "complete")
    partial = sum(1 for criterion in _CRITERIA if criterion.status == "partial")
    not_started = sum(1 for criterion in _CRITERIA if criterion.status == "not_started")
    overall_percent = round(sum(criterion.percent for criterion in _CRITERIA) / total)
    p1_criteria = tuple(criterion for criterion in _CRITERIA if criterion.required_for_p1)
    p1_gate_percent = round(sum(criterion.percent for criterion in p1_criteria) / len(p1_criteria))
    p1_blockers = tuple(
        criterion.criterion_id
        for criterion in p1_criteria
        if criterion.percent < 100
    )
    return AcceptanceSummary(
        total=total,
        complete=complete,
        partial=partial,
        not_started=not_started,
        overall_percent=overall_percent,
        p1_gate_percent=p1_gate_percent,
        p1_blockers=p1_blockers,
    )


def acceptance_dashboard_markdown() -> str:
    summary = acceptance_summary()
    lines = [
        "# P0 Acceptance Dashboard",
        "",
        f"- Overall reference completion: {summary.overall_percent}%",
        f"- P1 gate completion: {summary.p1_gate_percent}%",
        f"- Complete: {summary.complete}",
        f"- Partial: {summary.partial}",
        f"- Not started: {summary.not_started}",
        "",
        "| Criterion | Status | % | P1 Gate | Evidence | Next Action |",
        "| --- | --- | ---: | --- | --- | --- |",
    ]
    for criterion in _CRITERIA:
        evidence = ", ".join(f"`{item}`" for item in criterion.evidence)
        p1_gate = "yes" if criterion.required_for_p1 else "no"
        lines.append(
            f"| {criterion.title} | {criterion.status} | {criterion.percent}% | "
            f"{p1_gate} | {evidence} | {criterion.next_action} |"
        )
    return "\n".join(lines)
