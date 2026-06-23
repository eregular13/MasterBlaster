# Security Impact

## Change Summary

This change converts the application from a broad MCP/tool launcher into a Phase P0 authorized assessment simulator.

## Security-Relevant Effects

- Removed host command execution from MCP tabs.
- Disabled direct submodule script launching.
- Replaced Kali tool installation with reviewed manifest validation.
- Added deny-by-default policy checks for adapter identity, review state, arguments, target type, scope, network transport, engagement expiration, job expiration, and signatures.
- Added signed, expiring job envelopes that are independently validated by the runner simulator.
- Added deterministic fixture evidence with SHA-256 content hashes and parser provenance.
- Added a passive SQLite storage skeleton for validated runner results, evidence, and audit events.

## Privileged Behavior

P0 has no privileged live execution behavior. The only "run" action executes in-process fixture simulation after policy and signature validation. Persistence records outcomes after validation and does not authorize jobs.

## Residual Risk

The desktop UI still creates a local simulator engagement from the entered target for demonstration. Durable authorization workflows, tenant-aware application queries beyond the local skeleton, approval workflows, and MCP planning resources remain future P0 work.
