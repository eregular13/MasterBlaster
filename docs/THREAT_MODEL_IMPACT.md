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

## Trust Boundaries

The UI is not trusted for authorization. The runner simulator validates the signed envelope and re-evaluates policy before evidence is emitted.

Human approvals are not trusted because the UI displays them. The runner validates approval state, expiry, tenant, client, engagement, adapter, and target binding before issuing a job envelope.

The SQLite store is not trusted for authorization. It records runner outcomes after validation and is used only for local audit and report drafting.

P0 resources are not trusted for authorization. They are deterministic templates and checklist content only.

Acceptance criteria are not trusted for authorization. They document readiness and blockers only.

## Threats Reduced

- Arbitrary command execution through user-controlled flags or script paths.
- Accidental live target contact during local demos.
- Prompt or tool output injection influencing authorization, because fixture output is treated as data and the policy path is pure code.
- Unreviewed adapter execution, because manifests are enumerated in a closed registry.
- Lost in-memory audit context, because completed and denied simulator outcomes are persisted locally.
- Resource confusion, because unknown resource URIs fail closed and registered resources self-declare as non-executing content.
- Readiness inflation, because acceptance percentages are computed from explicit criteria with evidence links and blockers.
- Approval spoofing, because missing, denied, expired, or mismatched approvals fail closed before job issuance.

## Threats Remaining

- Persistent tenant/client/engagement storage is only a local skeleton.
- The local simulator signing key is process-local and intended only for demo validation.
- Report exports are Markdown drafts and still require downstream review before use.
- Future MCP exposure of resources still needs wrapper-level tests proving read-only behavior.
- CI does not yet generate an SBOM or enforce code-owner review for security-sensitive files.
