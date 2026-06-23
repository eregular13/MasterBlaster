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
- Added a closed non-executing P0 resource registry for planning, reporting, and governance templates.
- Added a machine-readable acceptance dashboard with evidence links and explicit P1 blockers.
- Added runner-enforced human approval artifacts before simulator job envelope issuance.

## Privileged Behavior

P0 has no privileged live execution behavior. The only "run" action executes in-process fixture simulation after policy, approval, and signature validation. Persistence records outcomes after validation and does not authorize jobs. Resources and acceptance criteria are inert governance content and cannot create or approve executable work.

## Residual Risk

The desktop UI still creates a local simulator engagement from the entered target for demonstration. Durable authorization workflows, tenant-aware application queries beyond the local skeleton, approval workflows, and an MCP wrapper around the non-executing resources remain future P0 work.
