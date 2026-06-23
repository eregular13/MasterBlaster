# P0 Acceptance Dashboard

This checklist gates discussion of any A2/A3 live capability. The source of truth is `masterblaster_control/p0_acceptance.py`; this document mirrors the current criteria and evidence links.

- Overall reference completion: 91%
- P1 gate completion: 100%
- Complete: 19
- Partial: 3
- Not started: 0

| Criterion | Status | % | P1 Gate | Evidence | Next Action |
| --- | --- | ---: | --- | --- | --- |
| Reviewed adapter manifest registry | complete | 100% | yes | `masterblaster_control/runner_simulator.py`, `tests/test_runner_simulator.py` | Add manifest signing metadata before live adapters exist. |
| Deterministic target parsing and scope decisions | complete | 100% | yes | `masterblaster_control/p0_policy.py`, `tests/test_p0_policy.py` | Add property-style target corpus tests. |
| Stable policy reason codes | complete | 100% | yes | `masterblaster_control/p0_policy.py` | Document reason-code contract in API docs. |
| Signed, expiring, bound job envelopes | complete | 100% | yes | `masterblaster_control/p0_models.py`, `masterblaster_control/p0_policy.py` | Add key-rotation design note. |
| Runner-side validation independent of UI | complete | 100% | yes | `masterblaster_control/runner_simulator.py`, `tests/test_runner_simulator.py` | Add runner request/response contract docs. |
| Offline A0 fixture inventory adapter | complete | 100% | yes | `masterblaster_control/runner_simulator.py` | Move fixture payloads to versioned fixture files. |
| A1 TLS assessment behind fake transport | complete | 100% | yes | `masterblaster_control/runner_simulator.py`, `tests/test_runner_simulator.py` | Add alternate TLS fixture scenarios. |
| Deterministic evidence hashes and parser provenance | complete | 100% | yes | `masterblaster_control/p0_models.py`, `tests/test_runner_simulator.py` | Add finding/mapping projection from evidence. |
| Persistent local audit for completed and denied outcomes | complete | 100% | yes | `masterblaster_control/p0_storage.py`, `masterblaster_control/p0_approvals.py`, `masterblaster_control/p0_retention.py`, `tests/test_p0_storage.py` | Add operator-configurable retention presets in the Qt settings panel. |
| Non-executing planning, reporting, governance resources | complete | 100% | yes | `masterblaster_control/p0_resources.py`, `tests/test_p0_resources.py` | Keep resource records transport-agnostic as the MCP facade evolves. |
| Negative tests for deny-by-default policy behavior | complete | 100% | yes | `tests/test_p0_policy.py` | Add mutation-style tests for policy bypass attempts. |
| Security impact and threat-model impact documentation | complete | 100% | yes | `docs/SECURITY_IMPACT.md`, `docs/THREAT_MODEL_IMPACT.md` | Add formal data-flow diagram doc. |
| Report drafts disclaim compliance certification | complete | 100% | yes | `README.md`, `ethics.md`, `masterblaster_control/utils.py` | Add report template snapshot tests. |
| Machine-readable acceptance dashboard | complete | 100% | yes | `masterblaster_control/p0_acceptance.py`, `tests/test_p0_acceptance.py` | Link dashboard rows to persisted evidence IDs. |
| Human approval state machine for simulator requests | complete | 100% | yes | `masterblaster_control/p0_approvals.py`, `masterblaster_control/runner_simulator.py`, `masterblaster_control/mcp_tab.py`, `tests/test_p0_approvals.py` | Add multi-approver and approval-policy configuration for future production use. |
| Tenant/client/engagement management UI over storage | partial | 35% | no | `masterblaster_control/p0_storage.py` | Add a read-only browser, then controlled create/edit forms. |
| MCP read-only wrapper for resources and draft tools | complete | 100% | yes | `masterblaster_control/p0_mcp_readonly.py`, `tests/test_p0_mcp_readonly.py`, `docs/architecture/p0-readonly-mcp.md` | Wrap the facade with an actual MCP transport after CI and review policy land. |
| Additional fixture adapters and parser scenarios | partial | 30% | no | `masterblaster_control/runner_simulator.py` | Add HTTP headers, DNS posture, and certificate-expiry fixture scenarios. |
| CI workflow for tests, dependency review, and SBOM stubs | complete | 100% | yes | `.github/workflows/p0-verification.yml`, `.github/workflows/dependency-review.yml`, `scripts/generate_sbom.py`, `sbom/masterblaster-p0.spdx.json`, `tests/test_sbom_generation.py`, `docs/supply-chain/sbom-and-dependency-review.md` | Enable dependency graph and required workflow checks in GitHub repository settings. |
| Review policy for security-sensitive files | complete | 100% | yes | `.github/CODEOWNERS`, `.github/pull_request_template.md`, `policy/security-sensitive-paths.json`, `scripts/validate_governance.py`, `tests/test_governance_review_policy.py`, `docs/governance/security-review-policy.md` | Enable CODEOWNERS-required review and branch protection in GitHub repository settings. |
| Storage retention and redaction policy | complete | 100% | yes | `masterblaster_control/p0_retention.py`, `masterblaster_control/p0_storage.py`, `tests/test_p0_retention.py`, `tests/test_p0_storage.py` | Add per-engagement retention overrides after management UI exists. |
| Rich audit and evidence browser in Qt UI | partial | 40% | no | `masterblaster_control/main_window.py` | Add filterable audit/evidence table widgets. |

## Hard Blockers For P1

- No live network transport.
- No host command execution.
- No arbitrary shell or user-supplied raw CLI arguments.
- No claims of compliance certification from simulator output.
- No adapter without a reviewed manifest and tests.
- GitHub repository settings must enforce required checks and CODEOWNERS review before production governance claims.
