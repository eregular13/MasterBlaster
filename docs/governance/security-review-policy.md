# Security Review Policy

## Required Reviewers

Security-sensitive changes must be reviewed by the repository owner listed in `policy/security-sensitive-paths.json`: `@eregular13`.

The canonical sensitive-path inventory covers policy, approval, signing, scope, evidence, simulator, MCP, registry, CI, dependency, retention, redaction, acceptance, documentation, and safety-test components.

## Separation Of Duties

Authors should not be the only reviewers of security-sensitive changes. For solo-maintainer emergency work, the exception must be documented in the pull request and in the follow-up audit trail.

## Prohibited Self-Approval

Self-approval is prohibited for changes that alter:

- adapter manifests or runner behavior;
- policy, scope parsing, approval validation, or job signing;
- evidence hashing or parser provenance;
- read-only MCP facade boundaries;
- CI workflows, dependency metadata, SBOM generation, or review policy;
- storage redaction or retention behavior.

## Emergency Changes

Emergency changes may be merged only when delaying would create greater risk. The pull request must document:

- the emergency condition;
- the reviewer or maintainer approving the exception;
- the exact files changed;
- the reduced verification performed before merge;
- the full verification and review follow-up required afterward.

## Required Evidence

Pull requests touching sensitive paths must include:

- security impact summary;
- threat-model impact summary;
- exact verification command output or CI links;
- dependency review status when dependencies changed;
- SBOM regeneration/check status when dependency metadata changed;
- confirmation that P0 remains simulator-only and draft-only.

## Threat-Model Update Triggers

Update `docs/THREAT_MODEL_IMPACT.md` when a change affects:

- trust boundaries;
- target, scope, approval, or tenant binding;
- signed envelope canonicalization;
- evidence hashing, parsing, or persistence;
- report generation;
- MCP resources or tools;
- CI, dependency review, SBOM generation, or governance checks.

## Dependency-Change Review

Dependency metadata changes must update all affected files in one change:

- `pyproject.toml`;
- `requirements.txt`;
- `sbom/masterblaster-p0.spdx.json`;
- relevant docs under `docs/supply-chain/`.

Run:

```bash
python scripts/generate_sbom.py
python scripts/generate_sbom.py --check
python scripts/validate_p0_registry.py
```

GitHub dependency review should also pass before merge when the repository feature is available.

## Exceptions

Exceptions must be recorded in the pull request template's `Exceptions` section with:

- reason;
- approving reviewer;
- compensating controls;
- follow-up issue or audit note;
- expiration date if the exception is temporary.

## Required Repository Settings

Repository maintainers should enable these GitHub settings. This repository can document and validate files, but it cannot prove remote enforcement unless checked through authenticated GitHub settings.

- Require pull request reviews before merging.
- Require CODEOWNERS review for matching files.
- Require status checks from `P0 Verification` and `Dependency Review`.
- Require branches to be up to date before merge.
- Restrict force pushes and branch deletion on the default branch.
- Enable dependency graph and Dependabot alerts where available.
- Require conversation resolution before merge.

## Machine Validation

Run the drift checker:

```bash
python scripts/validate_governance.py
```

The checker fails closed for malformed inventory JSON, missing CODEOWNERS coverage, conflicting CODEOWNERS entries, missing policy sections, and incomplete pull request templates.
