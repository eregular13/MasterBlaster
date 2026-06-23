# ADR 0002: A7 Live Adapter Governance

## Status

Proposed (P8 scaffold — not enabled in v1.0)

## Context

MasterBlaster v1.0 ships simulator-only adapters (a0–a6) with deny-by-default policy, human approvals, and fixture evidence. Operators will eventually request governed live transport for narrow assessment tasks (A7).

## Decision

A7 live adapters must satisfy all gates before registration:

1. **Reviewed manifest** with explicit `network_access: true`, allowed target types, and parameter allow-list.
2. **Rules of engagement** must set `allow_network_transport: true` for the engagement.
3. **Human approval** bound to engagement, adapter, and target before any live job envelope is signed.
4. **Rate limiting** via mock/live transport shim with audit events for every deny/allow.
5. **No shell execution** — live adapters are typed transports only; no subprocess or script launch.
6. **Pen-test pack** regression tests in `tests/test_adversarial_policy.py` must pass on every CI run.
7. **ADR + security review** required before merging any A7 manifest into `runner_simulator.MANIFESTS`.

## Consequences

- A7 remains blocked in v1.0; `evaluate_policy` already denies network transport without ROE consent.
- Future A7 work lands on `grok/masterblaster` with separate feature flags and additional acceptance criteria.
- Signed Windows installer and HSM key storage are P9 dependencies, not P8 blockers.