# MasterBlaster P0 Authorized Assessment Simulator

MasterBlaster is being narrowed into an authorized security assessment control plane. The current implementation is a Phase P0 simulator: it validates reviewed adapter manifests, deterministic target scope, signed expiring job envelopes, and hashed fixture evidence without running live tools or touching targets.

## Current P0 Capabilities

- Reviewed adapter manifest registry with deny-by-default lookup.
- Deterministic target parsing for host, domain, IP, CIDR, and HTTP(S) URL inputs.
- Scope and rules-of-engagement policy decisions with stable reason codes.
- Human approval artifacts validated by the runner before job issuance.
- Signed, expiring, tenant-bound, client-bound, engagement-bound, target-bound, and adapter-bound job envelopes.
- Runner simulator that independently validates policy and job signatures before emitting fixture evidence.
- One offline A0 fixture inventory adapter.
- One A1 TLS assessment adapter using a fake transport only.
- Evidence records with parser provenance, adapter version, and SHA-256 content hashes.
- SQLite persistence skeleton for tenants, clients, engagements, jobs, evidence, audit events, migrations, and report drafts.
- Recursive storage redaction and explicit retention purge controls for local simulator artifacts.
- Non-executing planning, reporting, and governance resources ready for a future MCP wrapper.
- Read-only MCP-shaped facade for registered resources, planning briefs, and simulator report drafts.
- Machine-readable P0 acceptance dashboard with evidence links and P1 blockers.
- Desktop UI for simulator runs, workflow ordering, audit logs, and report drafts.

## Non-Goals in P0

P0 does not install Kali tools, execute host commands, launch submodule scripts, scan networks, exploit services, brute-force credentials, collect secrets, or claim compliance. Unknown adapters, targets, arguments, and expired authorizations are denied.

## Quick Start

```bash
python -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
python main.py
```

Run the non-network test suite:

```bash
python -m pytest
```

Validate reviewed manifests from a shell:

```bash
python scripts/validate_p0_registry.py
```

The legacy `./scripts/verify_kali_tools.sh` wrapper is retained for compatibility, but it now delegates to the Python validator. It does not install packages.

Run the console demo:

```bash
python scripts/demo_p0_overdrive.py
```

The demo validates reviewed manifests and non-executing resources, runs one approved fixture simulator job and one denied approval path, records both outcomes in in-memory storage, previews redaction/retention controls, renders read-only MCP facade drafts, and prints acceptance blockers.

## Adapter Manifests

The reviewed P0 manifests live in `masterblaster_control/runner_simulator.py`:

- `a0.fixture.inventory`: offline fixture parser, no network transport.
- `a1.tls.assessment`: TLS parser behind a fake transport, no network transport.

All UI actions route through these manifests and the runner simulator. There is no generic command execution API.

## Local Storage

The desktop UI initializes `data/masterblaster_p0.sqlite3` for local simulator state. This database records runner results after policy validation:

- tenant, client, and engagement records;
- human approval artifacts;
- signed job envelopes for allowed simulator runs;
- hashed fixture evidence;
- audit events for both denied and completed runs;
- a migration table and report draft table skeleton.

The storage layer is deliberately passive. It does not authorize jobs, execute adapters, or override runner decisions.

JSON values are recursively redacted before persistence when they use sensitive key names or inline secret assignment patterns. Local retention controls can purge old approvals, jobs, evidence records, and audit events in dependency-safe order.

## Human Approval Gate

Simulator jobs require an approval artifact before the runner issues a signed envelope. The Qt UI asks for local human confirmation, but the runner still validates that the approval is approved, unexpired, and bound to the same tenant, client, engagement, adapter, and target.

Denied, expired, missing, or mismatched approvals fail closed.

## Non-Executing Resources

The P0 resource registry lives in `masterblaster_control/p0_resources.py`. It includes deterministic planning, reporting, and governance templates:

- `p0://planning/engagement-template`
- `p0://planning/rules-of-engagement-template`
- `p0://planning/workflow-template`
- `p0://reporting/report-draft-outline`
- `p0://governance/acceptance-checklist`

These resources are inert content. They can support UI and future MCP read operations, but they cannot execute jobs, approve scope, or override runner policy.

`masterblaster_control/p0_mcp_readonly.py` wraps these resources in a dependency-free, MCP-shaped facade. It exposes descriptor reads plus two draft renderers:

- `planning_brief`: a non-executing engagement planning brief.
- `report_draft`: a simulator-only report draft based on local audit/evidence summaries.

The facade has no job execution, approval mutation, adapter invocation, network transport, shell, or policy override surface.

## Acceptance Dashboard

The acceptance registry lives in `masterblaster_control/p0_acceptance.py` and renders `docs/P0_ACCEPTANCE_CHECKLIST.md`. It reports:

- overall reference completion;
- P1 gate completion;
- evidence files for each criterion;
- explicit blockers before any live-capability discussion.

The Qt Guardrails panel and report draft exports include the dashboard.

## Security Notes

- The UI is not a trusted authorization boundary; the runner re-validates each signed job envelope.
- Job signing keys are generated in memory for the local simulator and are not logged.
- Evidence content is deterministic fixture data and is hashed before report inclusion.
- Persistent audit records are local simulator artifacts and should not contain secrets.
- Storage redaction is defensive; secrets still must not be entered into simulator payloads.
- Reports are drafts and must not be represented as compliance certification.
- See `docs/P0_ACCEPTANCE_CHECKLIST.md` before discussing any P1 or live capability.

## Roadmap

Phase P0 should continue by adding tenant/client/engagement management UI, additional fixture adapters, CI dependency review, an SBOM workflow, and security-sensitive review policy. A2/A3 live capabilities remain out of scope until P0 acceptance criteria pass.
