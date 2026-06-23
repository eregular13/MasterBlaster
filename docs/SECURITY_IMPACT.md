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
- Added defensive storage redaction and deterministic retention purge controls.
- Added a dependency-free read-only MCP facade for resources, planning briefs, and simulator report drafts.
- Added deterministic SPDX SBOM generation/checks and least-privilege GitHub Actions workflow definitions.
- Added security-sensitive path inventory, CODEOWNERS routing, pull-request template, and governance drift validation.
- Added an AST-based prohibited-capability scanner for Python execution and network primitives.
- Hardened URL target parsing to reject userinfo, query strings, and fragments before simulator job issue.
- Hardened report draft writing to reject unsafe filesystem prefixes.
- Made the reviewed manifest registry read-only to external callers.

## Privileged Behavior

P0 has no privileged live execution behavior. The only "run" action executes in-process fixture simulation after policy, approval, and signature validation. Persistence records outcomes after validation and does not authorize jobs. Resources, acceptance criteria, SBOM/governance checks, and read-only MCP facade outputs are inert governance content and cannot create or approve executable work.

## Residual Risk

The desktop UI still creates a local simulator engagement from the entered target for demonstration. Durable authorization workflows, tenant-aware application queries beyond the local skeleton, and approval workflows remain future P0 work. A future network or stdio MCP transport must delegate to the read-only facade without adding job execution. GitHub branch protection, dependency graph availability, required status checks, and CODEOWNERS-required review must be enabled in repository settings before remote enforcement is claimed.
