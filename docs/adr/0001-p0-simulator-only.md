# ADR 0001: P0 Simulator-Only Execution

## Status

Accepted

## Context

The previous desktop control plane exposed broad security-tool and script-launching concepts before durable authorization, tenant isolation, reviewed adapter manifests, and runner validation were in place.

## Decision

Phase P0 execution is limited to in-process simulator adapters backed by reviewed manifests. Simulator jobs must be signed, expiring, engagement-bound, target-bound, adapter-bound, and independently validated by the runner before fixture evidence is emitted.

## Consequences

- The application cannot run live security tools in P0.
- Demonstrations remain deterministic and offline.
- Future live adapters must be added as narrow typed adapters with reviewed manifests and tests.
- A2/A3 capabilities remain blocked until P0 acceptance criteria pass.
