# Security-Sensitive Review Policy

This policy governs changes to MasterBlaster P0 before any live-capability discussion. It complements the deny-by-default simulator model and the P0 acceptance dashboard.

## Goals

- Keep authorization, policy, runner, and storage boundaries explicit and reviewed.
- Prevent accidental introduction of live execution, network transport, or shell surfaces.
- Ensure CI, SBOM, and dependency changes receive the same scrutiny as runtime code.

## Required Reviewers

Security-sensitive paths require review from a designated maintainer before merge. GitHub enforces this through `.github/CODEOWNERS` where branch protection is enabled.

## Security-Sensitive Paths

| Path | Why review is required |
| --- | --- |
| `masterblaster_control/runner_simulator.py` | Adapter manifest registry and simulator execution boundary |
| `masterblaster_control/p0_policy.py` | Target parsing, scope checks, job signing, deny reason codes |
| `masterblaster_control/p0_approvals.py` | Human approval gate and fail-closed validation |
| `masterblaster_control/p0_storage.py` | Persistent audit, evidence, and approval records |
| `masterblaster_control/p0_retention.py` | Redaction and retention purge behavior |
| `masterblaster_control/p0_mcp_readonly.py` | Read-only MCP facade; must not gain execution surface |
| `masterblaster_control/masterblaster_bridge.py` | Guardrails and policy presentation in the UI |
| `masterblaster_control/mcp_tab.py` | Simulator request path from UI into runner |
| `.github/workflows/` | CI, dependency review, and SBOM generation |
| `requirements.txt`, `pyproject.toml` | Dependency and packaging changes |
| `docs/SECURITY_IMPACT.md`, `docs/THREAT_MODEL_IMPACT.md` | Security and threat-model documentation |

## Review Checklist

Reviewers must confirm:

1. No live network transport, host command execution, or arbitrary shell arguments were added.
2. Unknown adapters, targets, arguments, and expired authorizations still fail closed.
3. The UI does not become a trusted authorization boundary.
4. Storage remains passive and does not authorize or execute jobs.
5. New adapters include reviewed manifests, fixture-only behavior, and tests.
6. Report drafts and MCP facade outputs remain non-certifying and read-only.

## Escalation

Changes that alter execution boundaries, signing semantics, or approval policy require an explicit note in `docs/SECURITY_IMPACT.md` and an updated row in `masterblaster_control/p0_acceptance.py` when applicable.

## Out of Scope

Cosmetic UI changes, documentation typos, and test-only fixture updates outside security-sensitive paths may use normal review, provided they do not touch the files listed above.