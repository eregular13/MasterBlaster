## Summary

- 

## Security impact

- [ ] No live scanning, probing, subprocess execution, network transport, unsafe import, or raw command surface added.
- [ ] UI, MCP, storage, and CI are not treated as trusted authorization boundaries.
- [ ] Unknown adapters, targets, arguments, tools, resources, scopes, and versions fail closed.

## Threat-model impact

- [ ] Trust boundaries are unchanged or documented.
- [ ] New privileged behavior is documented in `docs/SECURITY_IMPACT.md`.
- [ ] Threat-model changes are documented in `docs/THREAT_MODEL_IMPACT.md`.

## P0 invariant check

- [ ] Jobs remain signed, expiring, engagement-bound, target-bound, adapter-bound, and runner-validated.
- [ ] Evidence remains deterministic, hashed, and fixture-only.
- [ ] Report output remains draft-only and does not claim compliance certification.
- [ ] Read-only MCP resources/tools remain structurally incapable of execution.

## Verification

Paste exact command output or CI links:

```text
python -m pytest
python -m compileall masterblaster_control scripts
python scripts/validate_p0_registry.py
python scripts/demo_p0_overdrive.py
python scripts/generate_sbom.py --check
python scripts/validate_governance.py
python scripts/scan_prohibited_capabilities.py
```

## Dependency changes

- [ ] No dependency changes.
- [ ] Dependency changes are reflected in `requirements.txt`, `pyproject.toml`, and `sbom/masterblaster-p0.spdx.json`.
- [ ] GitHub dependency review and local SBOM check are expected to pass.

## Exceptions

Document any emergency exception, reviewer, compensating control, and follow-up issue:

- 
