from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from types import MappingProxyType
from typing import Callable, Literal

from .runner_simulator import MANIFESTS, validate_adapter_handler_registry

AcceptanceCategory = Literal["security", "execution", "evidence", "governance", "ux", "operations"]
AcceptanceStatus = Literal["complete", "partial", "not_started"]

REPO_ROOT = Path(__file__).resolve().parents[1]


class UnknownAcceptanceCriterionError(KeyError):
    pass


@dataclass(frozen=True)
class VerificationResult:
    verifier_id: str
    passed: bool
    reason: str
    external: bool = False

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class AcceptanceCriterionDefinition:
    criterion_id: str
    title: str
    category: AcceptanceCategory
    required_for_p1: bool
    evidence: tuple[str, ...]
    verifier_ids: tuple[str, ...]
    next_action: str


@dataclass(frozen=True)
class AcceptanceCriterion:
    criterion_id: str
    title: str
    category: AcceptanceCategory
    status: AcceptanceStatus
    percent: int
    required_for_p1: bool
    evidence: tuple[str, ...]
    verifier_ids: tuple[str, ...]
    failed_verifiers: tuple[VerificationResult, ...]
    next_action: str

    def to_dict(self) -> dict[str, object]:
        data = asdict(self)
        data["failed_verifiers"] = [result.to_dict() for result in self.failed_verifiers]
        return data


@dataclass(frozen=True)
class AcceptanceSummary:
    total: int
    complete: int
    partial: int
    not_started: int
    overall_percent: int
    p1_gate_percent: int
    p1_blockers: tuple[str, ...]


def _file_exists(relative_path: str) -> bool:
    return (REPO_ROOT / relative_path).exists()


def _read(relative_path: str) -> str:
    return (REPO_ROOT / relative_path).read_text(encoding="utf-8")


def _ok(verifier_id: str, reason: str = "passed", external: bool = False) -> VerificationResult:
    return VerificationResult(verifier_id, True, reason, external)


def _fail(verifier_id: str, reason: str, external: bool = False) -> VerificationResult:
    return VerificationResult(verifier_id, False, reason, external)


def _check_files(verifier_id: str, *paths: str) -> VerificationResult:
    missing = [path for path in paths if not _file_exists(path)]
    if missing:
        return _fail(verifier_id, f"Missing evidence path(s): {', '.join(missing)}")
    return _ok(verifier_id, "all evidence paths exist")


def _manifests_reviewed_offline(verifier_id: str) -> VerificationResult:
    if not isinstance(MANIFESTS, MappingProxyType):
        return _fail(verifier_id, "MANIFESTS is not exposed as a read-only mapping")
    for adapter_id, manifest in MANIFESTS.items():
        if not manifest.reviewed:
            return _fail(verifier_id, f"{adapter_id} is not reviewed")
        if manifest.network_access:
            return _fail(verifier_id, f"{adapter_id} declares network access")
        if not manifest.fixture_only:
            return _fail(verifier_id, f"{adapter_id} is not fixture-only")
    return _ok(verifier_id, "all manifests are reviewed, fixture-only, and no-network")


def _adapter_handlers_registered(verifier_id: str) -> VerificationResult:
    errors = validate_adapter_handler_registry()
    if errors:
        return _fail(verifier_id, "; ".join(errors))
    return _ok(verifier_id, "every manifest has an exact reviewed fixture handler and fixture file")


def _dependency_review_workflow_fail_closed(verifier_id: str) -> VerificationResult:
    workflow = _read(".github/workflows/dependency-review.yml")
    required = (
        "actions/dependency-review-action@a1d282b36b6f3519aa1f3fc636f609c47dddb294",
        "fail-on-severity: moderate",
        "python scripts/generate_sbom.py --check",
        "persist-credentials: false",
    )
    missing = [item for item in required if item not in workflow]
    if missing:
        return _fail(verifier_id, f"dependency workflow missing required item(s): {', '.join(missing)}")
    forbidden = ("continue-on-error", "|| true", "pull_request_target")
    present = [item for item in forbidden if item in workflow]
    if present:
        return _fail(verifier_id, f"dependency workflow contains fail-open or unsafe trigger item(s): {', '.join(present)}")
    return _ok(verifier_id, "dependency review workflow is configured to fail closed")


def _dependency_graph_verified(verifier_id: str) -> VerificationResult:
    return _fail(
        verifier_id,
        "GitHub Dependency graph/dependency-review enforcement is not verified from repository files; gh is unavailable in this environment",
        external=True,
    )


def _remote_review_enforcement_verified(verifier_id: str) -> VerificationResult:
    return _fail(
        verifier_id,
        "Branch protection, required checks, CODEOWNERS review, and conversation resolution are not verified from repository files",
        external=True,
    )


def _sbom_check(verifier_id: str) -> VerificationResult:
    from scripts.generate_sbom import DEFAULT_OUTPUT, check_sbom

    errors = check_sbom(DEFAULT_OUTPUT, REPO_ROOT)
    if errors:
        return _fail(verifier_id, "; ".join(errors))
    return _ok(verifier_id, "checked-in SPDX SBOM is current")


def _governance_check(verifier_id: str) -> VerificationResult:
    from scripts.validate_governance import validate_governance

    errors = validate_governance(REPO_ROOT)
    if errors:
        return _fail(verifier_id, "; ".join(errors))
    return _ok(verifier_id, "security review governance artifacts validate")


def _prohibited_capability_scan(verifier_id: str) -> VerificationResult:
    from scripts.scan_prohibited_capabilities import scan_paths

    findings = scan_paths((REPO_ROOT / "masterblaster_control", REPO_ROOT / "scripts", REPO_ROOT / "tests"))
    if findings:
        return _fail(verifier_id, "; ".join(finding.format(REPO_ROOT) for finding in findings))
    return _ok(verifier_id, "no prohibited Python execution/network primitives detected")


def _additional_fixture_adapters_present(verifier_id: str) -> VerificationResult:
    required = {"a2.http.headers", "a2.dns.posture", "a2.certificate.expiry"}
    missing = sorted(required - set(MANIFESTS))
    if missing:
        return _fail(verifier_id, f"missing additional fixture adapter manifest(s): {', '.join(missing)}")
    handler_errors = validate_adapter_handler_registry()
    if handler_errors:
        return _fail(verifier_id, "; ".join(handler_errors))
    return _ok(verifier_id, "additional fixture adapter manifests, handlers, and fixture files are registered")


def _tenant_management_ui_present(verifier_id: str) -> VerificationResult:
    text = _read("masterblaster_control/main_window.py")
    required = ("Tenant", "Client", "Engagement", "authorized_targets")
    missing = [item for item in required if item not in text]
    if missing:
        return _fail(verifier_id, f"tenant/client/engagement management UI markers missing: {', '.join(missing)}")
    return _ok(verifier_id, "tenant/client/engagement management UI markers are present")


def _audit_browser_filtering_present(verifier_id: str) -> VerificationResult:
    text = _read("masterblaster_control/main_window.py")
    required = ("AuditEvidenceBrowser", "filter", "date range", "tenant")
    missing = [item for item in required if item not in text]
    if missing:
        return _fail(verifier_id, f"audit/evidence browser markers missing: {', '.join(missing)}")
    return _ok(verifier_id, "basic audit/evidence display markers are present")


Verifier = Callable[[str], VerificationResult]

_VERIFIERS: dict[str, Verifier] = {
    "files.manifest_registry": lambda verifier_id: _check_files(verifier_id, "masterblaster_control/runner_simulator.py", "tests/test_runner_simulator.py"),
    "manifest.reviewed_offline": _manifests_reviewed_offline,
    "manifest.handlers_registered": _adapter_handlers_registered,
    "files.policy": lambda verifier_id: _check_files(verifier_id, "masterblaster_control/p0_policy.py", "tests/test_p0_policy.py"),
    "files.models": lambda verifier_id: _check_files(verifier_id, "masterblaster_control/p0_models.py"),
    "files.runner": lambda verifier_id: _check_files(verifier_id, "masterblaster_control/runner_simulator.py"),
    "files.evidence": lambda verifier_id: _check_files(verifier_id, "masterblaster_control/p0_models.py", "tests/test_runner_simulator.py"),
    "files.storage": lambda verifier_id: _check_files(verifier_id, "masterblaster_control/p0_storage.py", "tests/test_p0_storage.py"),
    "files.resources": lambda verifier_id: _check_files(verifier_id, "masterblaster_control/p0_resources.py", "tests/test_p0_resources.py"),
    "files.docs_security": lambda verifier_id: _check_files(verifier_id, "docs/SECURITY_IMPACT.md", "docs/THREAT_MODEL_IMPACT.md"),
    "files.report_disclaimer": lambda verifier_id: _check_files(verifier_id, "README.md", "ethics.md", "masterblaster_control/utils.py"),
    "files.acceptance": lambda verifier_id: _check_files(verifier_id, "masterblaster_control/p0_acceptance.py", "tests/test_p0_acceptance.py"),
    "files.approvals": lambda verifier_id: _check_files(verifier_id, "masterblaster_control/p0_approvals.py", "tests/test_p0_approvals.py"),
    "files.mcp_readonly": lambda verifier_id: _check_files(verifier_id, "masterblaster_control/p0_mcp_readonly.py", "tests/test_p0_mcp_readonly.py"),
    "files.retention": lambda verifier_id: _check_files(verifier_id, "masterblaster_control/p0_retention.py", "tests/test_p0_retention.py"),
    "ci.sbom.current": _sbom_check,
    "ci.dependency_review.fail_closed": _dependency_review_workflow_fail_closed,
    "external.dependency_graph.verified": _dependency_graph_verified,
    "governance.artifacts.valid": _governance_check,
    "external.remote_review_enforcement.verified": _remote_review_enforcement_verified,
    "security.prohibited_capability_scan": _prohibited_capability_scan,
    "ui.tenant_management.present": _tenant_management_ui_present,
    "adapters.additional_fixtures.present": _additional_fixture_adapters_present,
    "ui.audit_browser.basic": _audit_browser_filtering_present,
}


_DEFINITIONS: tuple[AcceptanceCriterionDefinition, ...] = (
    AcceptanceCriterionDefinition("manifest.reviewed_registry", "Reviewed adapter manifest registry", "security", True, ("masterblaster_control/runner_simulator.py", "tests/test_runner_simulator.py"), ("files.manifest_registry", "manifest.reviewed_offline", "manifest.handlers_registered"), "Add manifest signing metadata before live adapters exist."),
    AcceptanceCriterionDefinition("policy.scope_validation", "Deterministic target parsing and scope decisions", "security", True, ("masterblaster_control/p0_policy.py", "tests/test_p0_policy.py"), ("files.policy",), "Add property-style target corpus tests."),
    AcceptanceCriterionDefinition("policy.reason_codes", "Stable policy reason codes", "security", True, ("masterblaster_control/p0_policy.py",), ("files.policy",), "Document reason-code contract in API docs."),
    AcceptanceCriterionDefinition("jobs.signed_expiring_envelopes", "Signed, expiring, bound job envelopes", "execution", True, ("masterblaster_control/p0_models.py", "masterblaster_control/p0_policy.py"), ("files.models", "files.policy"), "Add key-rotation design note."),
    AcceptanceCriterionDefinition("runner.independent_validation", "Runner-side validation independent of UI", "execution", True, ("masterblaster_control/runner_simulator.py", "tests/test_runner_simulator.py"), ("files.runner",), "Add runner request/response contract docs."),
    AcceptanceCriterionDefinition("adapters.a0_fixture_inventory", "Offline A0 fixture inventory adapter", "execution", True, ("masterblaster_control/runner_simulator.py",), ("files.runner", "manifest.reviewed_offline"), "Move fixture payloads to versioned fixture files."),
    AcceptanceCriterionDefinition("adapters.a1_tls_fake_transport", "A1 TLS assessment behind fake transport", "execution", True, ("masterblaster_control/runner_simulator.py", "tests/test_runner_simulator.py"), ("files.runner", "manifest.reviewed_offline"), "Add alternate TLS fixture scenarios."),
    AcceptanceCriterionDefinition("evidence.hashing_provenance", "Deterministic evidence hashes and parser provenance", "evidence", True, ("masterblaster_control/p0_models.py", "tests/test_runner_simulator.py"), ("files.evidence",), "Add finding/mapping projection from evidence."),
    AcceptanceCriterionDefinition("storage.local_audit", "Persistent local audit for completed and denied outcomes", "evidence", True, ("masterblaster_control/p0_storage.py", "tests/test_p0_storage.py"), ("files.storage",), "Add operator-configurable retention presets in the Qt settings panel."),
    AcceptanceCriterionDefinition("resources.non_executing_registry", "Non-executing planning, reporting, governance resources", "governance", True, ("masterblaster_control/p0_resources.py", "tests/test_p0_resources.py"), ("files.resources",), "Keep resource records transport-agnostic as the MCP facade evolves."),
    AcceptanceCriterionDefinition("testing.negative_first", "Negative tests for deny-by-default policy behavior", "operations", True, ("tests/test_p0_policy.py",), ("files.policy",), "Add mutation-style tests for policy bypass attempts."),
    AcceptanceCriterionDefinition("docs.security_threat_model", "Security impact and threat-model impact documentation", "governance", True, ("docs/SECURITY_IMPACT.md", "docs/THREAT_MODEL_IMPACT.md"), ("files.docs_security",), "Add formal data-flow diagram doc."),
    AcceptanceCriterionDefinition("reports.draft_disclaimer", "Report drafts disclaim compliance certification", "governance", True, ("README.md", "ethics.md", "masterblaster_control/utils.py"), ("files.report_disclaimer",), "Add report template snapshot tests."),
    AcceptanceCriterionDefinition("governance.acceptance_dashboard", "Machine-readable acceptance dashboard", "governance", True, ("masterblaster_control/p0_acceptance.py", "tests/test_p0_acceptance.py"), ("files.acceptance",), "Link dashboard rows to persisted evidence IDs."),
    AcceptanceCriterionDefinition("approvals.human_gate", "Human approval state machine for simulator requests", "security", True, ("masterblaster_control/p0_approvals.py", "tests/test_p0_approvals.py"), ("files.approvals",), "Add multi-approver and approval-policy configuration for future production use."),
    AcceptanceCriterionDefinition("mcp.read_only_wrapper", "MCP read-only wrapper for resources and draft tools", "operations", True, ("masterblaster_control/p0_mcp_readonly.py", "tests/test_p0_mcp_readonly.py", "docs/architecture/p0-readonly-mcp.md"), ("files.mcp_readonly",), "Wrap the facade with an actual MCP transport after external gates are enforced."),
    AcceptanceCriterionDefinition("ci.sbom_drift", "Deterministic dependency metadata and SBOM drift gate", "operations", True, (".github/workflows/dependency-review.yml", "scripts/generate_sbom.py", "sbom/masterblaster-p0.spdx.json", "tests/test_sbom_generation.py"), ("ci.sbom.current",), "Generate a transitive hash-pinned lock artifact before production."),
    AcceptanceCriterionDefinition("ci.github_dependency_review", "GitHub dependency vulnerability review", "operations", True, (".github/workflows/dependency-review.yml", "tests/test_ci_workflows.py", "docs/supply-chain/sbom-and-dependency-review.md"), ("ci.dependency_review.fail_closed", "external.dependency_graph.verified"), "Enable Dependency graph and verify GitHub dependency review through repository settings."),
    AcceptanceCriterionDefinition("governance.review_policy_artifacts", "Repository-owned security review policy artifacts", "governance", True, (".github/CODEOWNERS", ".github/pull_request_template.md", "policy/security-sensitive-paths.json", "scripts/validate_governance.py", "tests/test_governance_review_policy.py", "docs/governance/security-review-policy.md"), ("governance.artifacts.valid",), "Bootstrap CODEOWNERS onto the base branch."),
    AcceptanceCriterionDefinition("governance.remote_enforcement", "Remote branch protection and CODEOWNERS enforcement", "governance", True, (".github/CODEOWNERS", "docs/governance/security-review-policy.md"), ("external.remote_review_enforcement.verified",), "Enable and verify branch protection, required checks, CODEOWNERS review, and conversation resolution."),
    AcceptanceCriterionDefinition("storage.retention_redaction", "Storage retention and redaction policy", "security", True, ("masterblaster_control/p0_retention.py", "tests/test_p0_retention.py"), ("files.retention",), "Add per-engagement retention overrides after management UI exists."),
    AcceptanceCriterionDefinition("security.prohibited_capability_scan", "Repository prohibited-capability scan", "security", True, ("scripts/scan_prohibited_capabilities.py", "tests/test_prohibited_capability_scanner.py"), ("security.prohibited_capability_scan",), "Expand scanning to non-Python shipped surfaces."),
    AcceptanceCriterionDefinition("ui.tenant_engagement_management", "Tenant/client/engagement management UI over storage", "ux", False, ("masterblaster_control/p0_storage.py", "masterblaster_control/main_window.py"), ("files.storage", "ui.tenant_management.present"), "Add persisted tenant/client/engagement management forms and require selected engagements for runs."),
    AcceptanceCriterionDefinition("adapters.additional_fixtures", "Additional fixture adapters and parser scenarios", "execution", False, ("masterblaster_control/runner_simulator.py", "masterblaster_control/fixtures/a2_http_headers.json", "masterblaster_control/fixtures/a2_dns_posture.json", "masterblaster_control/fixtures/a2_certificate_expiry.json"), ("adapters.additional_fixtures.present",), "Add finding/mapping projection from the new fixture evidence."),
    AcceptanceCriterionDefinition("ui.audit_browser", "Rich audit and evidence browser in Qt UI", "ux", False, ("masterblaster_control/main_window.py",), ("ui.audit_browser.basic",), "Add filterable audit/evidence table widgets."),
)

_DEFINITION_BY_ID = {definition.criterion_id: definition for definition in _DEFINITIONS}


def run_verifier(verifier_id: str) -> VerificationResult:
    verifier = _VERIFIERS.get(verifier_id)
    if verifier is None:
        return _fail(verifier_id, "unknown verifier")
    try:
        return verifier(verifier_id)
    except Exception as exc:
        return _fail(verifier_id, f"verifier raised {type(exc).__name__}: {exc}")


def _materialize(definition: AcceptanceCriterionDefinition) -> AcceptanceCriterion:
    evidence_result = _check_files(f"{definition.criterion_id}.evidence", *definition.evidence)
    results = (evidence_result,) + tuple(run_verifier(verifier_id) for verifier_id in definition.verifier_ids)
    passed = sum(1 for result in results if result.passed)
    percent = round((passed / len(results)) * 100)
    if passed == len(results):
        status: AcceptanceStatus = "complete"
    elif passed == 0:
        status = "not_started"
    else:
        status = "partial"
    return AcceptanceCriterion(
        criterion_id=definition.criterion_id,
        title=definition.title,
        category=definition.category,
        status=status,
        percent=percent,
        required_for_p1=definition.required_for_p1,
        evidence=definition.evidence,
        verifier_ids=definition.verifier_ids,
        failed_verifiers=tuple(result for result in results if not result.passed),
        next_action=definition.next_action,
    )


def list_acceptance_criteria() -> tuple[AcceptanceCriterion, ...]:
    return tuple(_materialize(definition) for definition in _DEFINITIONS)


def read_acceptance_criterion(criterion_id: str) -> AcceptanceCriterion:
    try:
        return _materialize(_DEFINITION_BY_ID[criterion_id])
    except KeyError as exc:
        raise UnknownAcceptanceCriterionError(f"Unknown acceptance criterion: {criterion_id}") from exc


def acceptance_summary() -> AcceptanceSummary:
    criteria = list_acceptance_criteria()
    total = len(criteria)
    complete = sum(1 for criterion in criteria if criterion.status == "complete")
    partial = sum(1 for criterion in criteria if criterion.status == "partial")
    not_started = sum(1 for criterion in criteria if criterion.status == "not_started")
    overall_percent = round(sum(criterion.percent for criterion in criteria) / total)
    p1_criteria = tuple(criterion for criterion in criteria if criterion.required_for_p1)
    p1_gate_percent = round(sum(criterion.percent for criterion in p1_criteria) / len(p1_criteria))
    p1_blockers = tuple(criterion.criterion_id for criterion in p1_criteria if criterion.percent < 100)
    return AcceptanceSummary(total, complete, partial, not_started, overall_percent, p1_gate_percent, p1_blockers)


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
        "| Criterion | Status | % | P1 Gate | Evidence | Failed Verifiers | Next Action |",
        "| --- | --- | ---: | --- | --- | --- | --- |",
    ]
    for criterion in list_acceptance_criteria():
        evidence = ", ".join(f"`{item}`" for item in criterion.evidence)
        p1_gate = "yes" if criterion.required_for_p1 else "no"
        failed = "<br>".join(
            f"`{result.verifier_id}`: {result.reason}" for result in criterion.failed_verifiers
        ) or "none"
        lines.append(
            f"| {criterion.title} | {criterion.status} | {criterion.percent}% | "
            f"{p1_gate} | {evidence} | {failed} | {criterion.next_action} |"
        )
    return "\n".join(lines)


def acceptance_dashboard_json() -> str:
    return json.dumps(
        {
            "summary": asdict(acceptance_summary()),
            "criteria": [criterion.to_dict() for criterion in list_acceptance_criteria()],
        },
        indent=2,
        sort_keys=True,
    ) + "\n"
