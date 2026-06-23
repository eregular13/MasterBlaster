# Threat Model Impact

## Assets Protected

- Local workstation integrity.
- Engagement scope and authorization decisions.
- Simulator job envelopes.
- Human approval artifacts.
- Evidence provenance and report drafts.
- Local SQLite audit history.
- Non-executing planning, reporting, and governance resources.
- Acceptance dashboard criteria and evidence links.
- Storage redaction and retention policy.
- Read-only MCP facade descriptors and draft renderers.
- CI workflow definitions, dependency metadata, deterministic SBOM, CODEOWNERS, PR template, and governance policy.
- Prohibited-capability scanner rules and findings.

## Trust Boundaries

The UI is not trusted for authorization. The runner simulator validates the signed envelope and re-evaluates policy before evidence is emitted. The desktop UI must select a persisted engagement before requesting a simulator job.

Human approvals are not trusted because the UI displays them. The runner validates approval state, expiry, replay, tenant, client, engagement, adapter, and target binding before issuing a job envelope.

The SQLite store is not trusted for authorization. It records runner outcomes after validation and is used only for local engagement selection, audit, evidence browsing, and report drafting.

P0 resources are not trusted for authorization. They are deterministic templates and checklist content only.

Acceptance criteria are not trusted for authorization. They document readiness and blockers only.

Redaction is not trusted as permission to collect secrets. It is a fail-soft persistence guard for accidental sensitive keys or inline secret-like strings.

The read-only MCP facade is not trusted for authorization. It can render deterministic planning/report drafts and read registered resources, but it cannot issue jobs, approve scope, invoke adapters, contact targets, or override runner policy.

CI and governance files are not trusted authorization boundaries. They provide reproducible review and drift signals; the runner remains the enforcement boundary for simulator jobs.

## Threats Reduced

- Arbitrary command execution through user-controlled flags or script paths.
- Accidental live target contact during local demos.
- Prompt or tool output injection influencing authorization, because fixture output is treated as data and the policy path is pure code.
- Unreviewed adapter execution, because manifests are enumerated in a closed registry.
- Lost in-memory audit context, because completed and denied simulator outcomes are persisted locally.
- Resource confusion, because unknown resource URIs fail closed and registered resources self-declare as non-executing content.
- Readiness inflation, because acceptance percentages are computed from explicit criteria with evidence links and blockers.
- Approval spoofing, because missing, denied, expired, or mismatched approvals fail closed before job issuance.
- Local artifact over-retention, because old approvals, jobs, evidence, and audit events can be purged in dependency-safe order.
- MCP surface creep, because the facade only exposes resource reads and draft renderers and unknown tool names fail closed.
- Secret-bearing or ambiguous URL targets, because userinfo, query strings, and fragments are rejected before job issue.
- Mutable registry tampering, because the reviewed manifest registry is exposed as a read-only mapping.
- Manifest/handler drift, because every reviewed manifest must have an exact immutable fixture handler and checked-in fixture file.
- Cross-tenant evidence browsing, because ordinary audit/evidence reads require tenant scope and global reads are explicit admin methods.
- Supply-chain drift, because SBOM check mode fails when dependency metadata changes without regenerated SPDX output.
- Governance drift, because CODEOWNERS, sensitive-path inventory, policy docs, and PR templates are machine-validated.
- Reintroduction of Python execution/network primitives, because the AST scanner fails on representative forbidden constructs.

## Threats Remaining

- Persistent tenant/client/engagement management is a local simulator workflow, not a production multi-operator authorization workflow.
- The local simulator signing key is process-local and intended only for demo validation.
- Report exports are Markdown drafts and still require downstream review before use.
- A future MCP network or stdio transport still needs integration tests proving it delegates only to the read-only facade.
- GitHub remote enforcement settings cannot be proven from repository files alone; maintainers must enable required checks, dependency graph support, and CODEOWNERS-required review. Without Dependency graph support, GitHub dependency review fails closed and cannot be claimed as active vulnerability enforcement.
