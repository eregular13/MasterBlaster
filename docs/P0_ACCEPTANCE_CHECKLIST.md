# P0 Acceptance Checklist

This checklist gates discussion of any A2/A3 live capability. Every item must remain true before the project can move beyond simulator-only operation.

## Implemented

- [x] Reviewed adapter manifest registry.
- [x] Deterministic target parsing and scope decisions.
- [x] Stable policy reason codes.
- [x] Signed, expiring, tenant-bound, client-bound, engagement-bound, target-bound, adapter-bound job envelopes.
- [x] Runner-side validation independent of the UI.
- [x] Offline A0 fixture inventory adapter.
- [x] A1 TLS assessment adapter behind fake transport only.
- [x] Deterministic fixture evidence with SHA-256 hashes and parser provenance.
- [x] Persistent local audit records for completed and denied simulator outcomes.
- [x] Non-executing planning, reporting, and governance resources.
- [x] Negative tests for deny-by-default policy behavior.
- [x] Security impact and threat-model impact documentation.
- [x] Explicit report draft disclaimer.

## Remaining P0 Work

- [ ] Human approval state machine for simulator job requests.
- [ ] Tenant/client/engagement management UI over the local storage skeleton.
- [ ] MCP service wrapper exposing resources and draft-only planning/reporting tools.
- [ ] Additional fixture adapters and parser scenarios.
- [ ] CI workflow for tests, dependency review, and SBOM artifact generation.
- [ ] Code-owner or review-policy documentation for sensitive files.
- [ ] Storage retention and redaction policy.
- [ ] Rich audit/event browser in the Qt UI.

## Hard Blockers For P1

- No live network transport.
- No host command execution.
- No arbitrary shell or user-supplied raw CLI arguments.
- No claims of compliance certification from simulator output.
- No adapter without a reviewed manifest and tests.
