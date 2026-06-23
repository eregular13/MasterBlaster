# P0 Final-Boss Hardening Audit - 2026-06-23

## Scope Reviewed

- Runner simulator, reviewed adapter registry, policy evaluation, target parsing, job signing, evidence hashing, and approval validation.
- Storage, retention, redaction, report draft writing, and local audit persistence.
- Non-executing resource registry and read-only MCP facade.
- Acceptance registry, registry validator, demo script, README, security impact, threat model, and architecture docs.
- Dependency metadata, SBOM generation, GitHub Actions workflows, CODEOWNERS, PR template, and security review policy.
- Existing and new tests for policy, approvals, storage, retention, resources, MCP facade, SBOM, governance, prohibited capabilities, and report filesystem safety.

## Threats Considered

- Unknown MCP resources or read-only tool names.
- Side-effectful callables entering the read-only MCP facade.
- Descriptor and implementation mismatches.
- Mutable registry tampering.
- Approval bypass through missing, denied, expired, replayed, or mismatched approvals.
- Signature confusion and non-canonical signed data.
- Evidence substitution or hash mismatch.
- Job, tenant, client, or engagement cross-contamination.
- Target canonicalization ambiguity, including URL userinfo, query strings, and fragments.
- Report path traversal or absolute-path injection.
- Retention bypass and incomplete redaction.
- Secrets in logs, reports, exceptions, SBOMs, or CI artifacts.
- Nondeterministic SBOM output.
- Fail-open validation behavior.
- Platform-specific path assumptions.
- Dangerous imports, unsafe deserialization, arbitrary subprocess, network primitives, or shell execution.
- Documentation claims not backed by executable checks.

## Findings Fixed

| Finding | Risk | Fix | Regression Evidence |
| --- | --- | --- | --- |
| Reviewed manifest registry was externally mutable. | In-process callers could mutate adapter registry state before policy evaluation. | Exposed `MANIFESTS` as a read-only `MappingProxyType`. | `tests/test_runner_simulator.py::test_manifest_registry_is_immutable_to_callers` |
| URL targets accepted userinfo, query strings, and fragments before normalization. | Secret-bearing or ambiguous target strings could enter logs or approval prompts. | `parse_target` now rejects URL userinfo, query strings, and fragments. | `tests/test_p0_policy.py::test_url_targets_reject_secret_or_ambiguous_components` |
| Report helper accepted arbitrary prefixes. | Future callers could accidentally create path traversal or absolute-path writes. | Report prefixes now require a safe lowercase slug and writes stay under `reports/`. | `tests/test_utils.py` |
| Prohibited capability checks were ad hoc text sweeps. | String checks could miss AST constructs or flag harmless docs. | Added AST scanner for forbidden imports, calls, names, and `shell=True`. | `scripts/scan_prohibited_capabilities.py`, `tests/test_prohibited_capability_scanner.py` |
| CI/SBOM and review policy blockers lacked reproducible enforcement. | P1 gate depended on documentation rather than machine-checkable artifacts. | Added pinned GitHub Actions workflows, deterministic SPDX SBOM, SBOM check mode, CODEOWNERS, PR template, sensitive-path inventory, and governance validator. | `scripts/generate_sbom.py`, `scripts/validate_governance.py`, `tests/test_sbom_generation.py`, `tests/test_governance_review_policy.py` |

## Residual Risks

- GitHub branch protection, required status checks, dependency graph support, and CODEOWNERS-required review are external repository settings. The repository files document the required settings but cannot prove they are enabled.
- Persistent tenant/client/engagement management remains a local skeleton rather than a production authorization workflow.
- The local simulator signing key is process-local and intended for P0 demo validation only.
- Report exports remain Markdown drafts requiring human review.
- Any future MCP network or stdio transport must delegate only to `P0ReadOnlyMCPFacade` and must receive separate integration tests.

## External Configuration Still Required

- Enable required pull request review.
- Enable CODEOWNERS-required review.
- Require `P0 Verification` and `Dependency Review` checks before merge.
- Enable dependency graph and Dependabot alerts where available.
- Protect the default branch from force pushes and deletion.
- Require conversation resolution before merge.

## Verification Commands

Executed on Windows with Python 3.14.6:

```text
python -m pytest
python -m compileall masterblaster_control scripts
python scripts\validate_p0_registry.py
python scripts\demo_p0_overdrive.py
python scripts\generate_sbom.py --check
python scripts\validate_governance.py
python scripts\scan_prohibited_capabilities.py
```

Observed results:

- `python -m pytest` -> 53 passed.
- `python -m compileall masterblaster_control scripts` -> succeeded.
- `python scripts\validate_p0_registry.py` -> 2 reviewed manifests, 5 non-executing resources, deterministic SPDX SBOM, governance artifacts, prohibited-capability scan, 91% overall, 100% P1 gate, 0 blockers.
- `python scripts\demo_p0_overdrive.py` -> approved fixture run, denied approval path, redaction preview, retention purge preview, read-only MCP drafts, 100% P1 gate.
- `python scripts\generate_sbom.py --check` -> succeeded.
- `python scripts\validate_governance.py` -> succeeded.
- `python scripts\scan_prohibited_capabilities.py` -> succeeded.
- SBOM regenerated without hash drift: `CFF32464B6A103ED9E62EB681414E522496338E7B60451DDAA214DA0A82C06E3`.

## Why The System Remains Non-Executing

- No adapter manifest declares network access.
- The runner simulator requires policy allow, human approval, signed envelope validation, expiry validation, and scope validation before emitting fixture evidence.
- The read-only MCP facade has no runner import and exposes only resource reads and draft renderers.
- CI, SBOM, governance, and scanner scripts inspect repository state; they do not execute adapters, contact targets, approve jobs, or alter runner policy.
- Report outputs are watermarked drafts and cannot certify compliance.
