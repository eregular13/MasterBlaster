# Threat Model Impact

## Assets Protected

- Local workstation integrity.
- Engagement scope and authorization decisions.
- Simulator job envelopes.
- Evidence provenance and report drafts.
- Local SQLite audit history.

## Trust Boundaries

The UI is not trusted for authorization. The runner simulator validates the signed envelope and re-evaluates policy before evidence is emitted.

The SQLite store is not trusted for authorization. It records runner outcomes after validation and is used only for local audit and report drafting.

## Threats Reduced

- Arbitrary command execution through user-controlled flags or script paths.
- Accidental live target contact during local demos.
- Prompt or tool output injection influencing authorization, because fixture output is treated as data and the policy path is pure code.
- Unreviewed adapter execution, because manifests are enumerated in a closed registry.
- Lost in-memory audit context, because completed and denied simulator outcomes are persisted locally.

## Threats Remaining

- Persistent tenant/client/engagement storage is only a local skeleton.
- The local simulator signing key is process-local and intended only for demo validation.
- Report exports are Markdown drafts and still require downstream review before use.
- CI does not yet generate an SBOM or enforce code-owner review for security-sensitive files.
