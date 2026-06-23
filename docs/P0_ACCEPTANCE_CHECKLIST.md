# P0 Acceptance Dashboard

This checklist gates discussion of any A2/A3 live capability. The source of truth is `masterblaster_control/p0_acceptance.py`; this document mirrors verifier-derived criteria, evidence links, and failed-verifier reasons.

- Overall reference completion: 97%
- P1 gate completion: 96%
- Complete: 23
- Partial: 2
- Not started: 0

| Criterion | Status | % | P1 Gate | Evidence | Failed Verifiers | Next Action |
| --- | --- | ---: | --- | --- | --- | --- |
| Reviewed adapter manifest registry | complete | 100% | yes | `masterblaster_control/runner_simulator.py`, `tests/test_runner_simulator.py` | none | Add manifest signing metadata before live adapters exist. |
| Deterministic target parsing and scope decisions | complete | 100% | yes | `masterblaster_control/p0_policy.py`, `tests/test_p0_policy.py` | none | Add property-style target corpus tests. |
| Stable policy reason codes | complete | 100% | yes | `masterblaster_control/p0_policy.py` | none | Document reason-code contract in API docs. |
| Signed, expiring, bound job envelopes | complete | 100% | yes | `masterblaster_control/p0_models.py`, `masterblaster_control/p0_policy.py` | none | Add key-rotation design note. |
| Runner-side validation independent of UI | complete | 100% | yes | `masterblaster_control/runner_simulator.py`, `tests/test_runner_simulator.py` | none | Add runner request/response contract docs. |
| Offline A0 fixture inventory adapter | complete | 100% | yes | `masterblaster_control/runner_simulator.py` | none | Move fixture payloads to versioned fixture files. |
| A1 TLS assessment behind fake transport | complete | 100% | yes | `masterblaster_control/runner_simulator.py`, `tests/test_runner_simulator.py` | none | Add alternate TLS fixture scenarios. |
| Deterministic evidence hashes and parser provenance | complete | 100% | yes | `masterblaster_control/p0_models.py`, `tests/test_runner_simulator.py` | none | Add finding/mapping projection from evidence. |
| Persistent local audit for completed and denied outcomes | complete | 100% | yes | `masterblaster_control/p0_storage.py`, `tests/test_p0_storage.py` | none | Add operator-configurable retention presets in the Qt settings panel. |
| Non-executing planning, reporting, governance resources | complete | 100% | yes | `masterblaster_control/p0_resources.py`, `tests/test_p0_resources.py` | none | Keep resource records transport-agnostic as the MCP facade evolves. |
| Negative tests for deny-by-default policy behavior | complete | 100% | yes | `tests/test_p0_policy.py` | none | Add mutation-style tests for policy bypass attempts. |
| Security impact and threat-model impact documentation | complete | 100% | yes | `docs/SECURITY_IMPACT.md`, `docs/THREAT_MODEL_IMPACT.md` | none | Add formal data-flow diagram doc. |
| Report drafts disclaim compliance certification | complete | 100% | yes | `README.md`, `ethics.md`, `masterblaster_control/utils.py` | none | Add report template snapshot tests. |
| Machine-readable acceptance dashboard | complete | 100% | yes | `masterblaster_control/p0_acceptance.py`, `tests/test_p0_acceptance.py` | none | Link dashboard rows to persisted evidence IDs. |
| Human approval state machine for simulator requests | complete | 100% | yes | `masterblaster_control/p0_approvals.py`, `tests/test_p0_approvals.py` | none | Add multi-approver and approval-policy configuration for future production use. |
| MCP read-only wrapper for resources and draft tools | complete | 100% | yes | `masterblaster_control/p0_mcp_readonly.py`, `tests/test_p0_mcp_readonly.py`, `docs/architecture/p0-readonly-mcp.md` | none | Wrap the facade with an actual MCP transport after external gates are enforced. |
| Deterministic dependency metadata and SBOM drift gate | complete | 100% | yes | `.github/workflows/dependency-review.yml`, `scripts/generate_sbom.py`, `sbom/masterblaster-p0.spdx.json`, `tests/test_sbom_generation.py` | none | Generate a transitive hash-pinned lock artifact before production. |
| GitHub dependency vulnerability review | partial | 67% | yes | `.github/workflows/dependency-review.yml`, `tests/test_ci_workflows.py`, `docs/supply-chain/sbom-and-dependency-review.md` | `external.dependency_graph.verified`: GitHub Dependency graph/dependency-review enforcement is not verified from repository files; gh is unavailable in this environment | Enable Dependency graph and verify GitHub dependency review through repository settings. |
| Repository-owned security review policy artifacts | complete | 100% | yes | `.github/CODEOWNERS`, `.github/pull_request_template.md`, `policy/security-sensitive-paths.json`, `scripts/validate_governance.py`, `tests/test_governance_review_policy.py`, `docs/governance/security-review-policy.md` | none | Bootstrap CODEOWNERS onto the base branch. |
| Remote branch protection and CODEOWNERS enforcement | partial | 50% | yes | `.github/CODEOWNERS`, `docs/governance/security-review-policy.md` | `external.remote_review_enforcement.verified`: Branch protection, required checks, CODEOWNERS review, and conversation resolution are not verified from repository files | Enable and verify branch protection, required checks, CODEOWNERS review, and conversation resolution. |
| Storage retention and redaction policy | complete | 100% | yes | `masterblaster_control/p0_retention.py`, `tests/test_p0_retention.py` | none | Add per-engagement retention overrides after management UI exists. |
| Repository prohibited-capability scan | complete | 100% | yes | `scripts/scan_prohibited_capabilities.py`, `tests/test_prohibited_capability_scanner.py` | none | Expand scanning to non-Python shipped surfaces. |
| Tenant/client/engagement management UI over storage | complete | 100% | no | `masterblaster_control/p0_storage.py`, `masterblaster_control/main_window.py` | none | Add persisted tenant/client/engagement management forms and require selected engagements for runs. |
| Additional fixture adapters and parser scenarios | complete | 100% | no | `masterblaster_control/runner_simulator.py`, `masterblaster_control/fixtures/a2_http_headers.json`, `masterblaster_control/fixtures/a2_dns_posture.json`, `masterblaster_control/fixtures/a2_certificate_expiry.json` | none | Add finding/mapping projection from the new fixture evidence. |
| Rich audit and evidence browser in Qt UI | complete | 100% | no | `masterblaster_control/main_window.py` | none | Add filterable audit/evidence table widgets. |
