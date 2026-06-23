# P0 Acceptance Dashboard

This checklist gates discussion of any A2/A3 live capability. The source of truth is `masterblaster_control/p0_acceptance.py`; this document mirrors the current criteria and evidence links.

- Overall reference completion: 72%
- P1 gate completion: 78%
- Complete: 14
- Partial: 4
- Not started: 4

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
| Persistent local audit for completed and denied outcomes | partial | 90% | yes | `masterblaster_control/p0_storage.py`, `masterblaster_control/p0_approvals.py`, `tests/test_p0_storage.py` | Add retention and redaction controls. |
| Non-executing planning, reporting, governance resources | complete | 100% | yes | `masterblaster_control/p0_resources.py`, `tests/test_p0_resources.py` | Wrap resources in an MCP read-only service. |
| Negative tests for deny-by-default policy behavior | complete | 100% | yes | `tests/test_p0_policy.py` | Add mutation-style tests for policy bypass attempts. |
| Security impact and threat-model impact documentation | complete | 100% | yes | `docs/SECURITY_IMPACT.md`, `docs/THREAT_MODEL_IMPACT.md` | Add formal data-flow diagram doc. |
| Report drafts disclaim compliance certification | complete | 100% | yes | `README.md`, `ethics.md`, `masterblaster_control/utils.py` | Add report template snapshot tests. |
| Machine-readable acceptance dashboard | complete | 100% | yes | `masterblaster_control/p0_acceptance.py`, `tests/test_p0_acceptance.py` | Link dashboard rows to persisted evidence IDs. |
| Human approval state machine for simulator requests | complete | 100% | yes | `masterblaster_control/p0_approvals.py`, `masterblaster_control/runner_simulator.py`, `masterblaster_control/mcp_tab.py`, `tests/test_p0_approvals.py` | Add multi-approver and approval-policy configuration for future production use. |
| Tenant/client/engagement management UI over storage | partial | 35% | no | `masterblaster_control/p0_storage.py` | Add a read-only browser, then controlled create/edit forms. |
| MCP read-only wrapper for resources and draft tools | not_started | 0% | yes | `docs/architecture/p0-resources.md` | Create service skeleton that exposes resources but cannot execute jobs. |
| Additional fixture adapters and parser scenarios | partial | 30% | no | `masterblaster_control/runner_simulator.py` | Add HTTP headers, DNS posture, and certificate-expiry fixture scenarios. |
| CI workflow for tests, dependency review, and SBOM stubs | not_started | 0% | yes | `docs/P0_ACCEPTANCE_CHECKLIST.md` | Add GitHub Actions workflow plus generated SBOM placeholder. |
| Review policy for security-sensitive files | not_started | 0% | yes | `docs/P0_ACCEPTANCE_CHECKLIST.md` | Add CODEOWNERS-style policy documentation. |
| Storage retention and redaction policy | not_started | 0% | yes | `docs/architecture/p0-storage.md` | Add redaction helpers and retention settings. |
| Rich audit and evidence browser in Qt UI | partial | 40% | no | `masterblaster_control/main_window.py` | Add filterable audit/evidence table widgets. |

## Hard Blockers For P1

- No live network transport.
- No host command execution.
- No arbitrary shell or user-supplied raw CLI arguments.
- No claims of compliance certification from simulator output.
- No adapter without a reviewed manifest and tests.
- Read-only MCP wrapper, CI/SBOM, review policy, and retention/redaction controls must be completed.
