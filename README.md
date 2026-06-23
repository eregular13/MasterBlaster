# MasterBlaster P0 Authorized Assessment Simulator

MasterBlaster is being narrowed into an authorized security assessment control plane. The current implementation is a Phase P0 simulator: it validates reviewed adapter manifests, deterministic target scope, signed expiring job envelopes, and hashed fixture evidence without running live tools or touching targets.

## Current P0 Capabilities

- Reviewed adapter manifest registry with deny-by-default lookup.
- Deterministic target parsing for host, domain, IP, CIDR, and HTTP(S) URL inputs.
- Scope and rules-of-engagement policy decisions with stable reason codes.
- Signed, expiring, tenant-bound, client-bound, engagement-bound, target-bound, and adapter-bound job envelopes.
- Runner simulator that independently validates policy and job signatures before emitting fixture evidence.
- One offline A0 fixture inventory adapter.
- One A1 TLS assessment adapter using a fake transport only.
- Evidence records with parser provenance, adapter version, and SHA-256 content hashes.
- SQLite persistence skeleton for tenants, clients, engagements, jobs, evidence, audit events, migrations, and report drafts.
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
./scripts/verify_kali_tools.sh
```

The script name is retained for compatibility, but it now validates P0 manifests only. It does not install packages.

## Adapter Manifests

The reviewed P0 manifests live in `masterblaster_control/runner_simulator.py`:

- `a0.fixture.inventory`: offline fixture parser, no network transport.
- `a1.tls.assessment`: TLS parser behind a fake transport, no network transport.

All UI actions route through these manifests and the runner simulator. There is no generic command execution API.

## Local Storage

The desktop UI initializes `data/masterblaster_p0.sqlite3` for local simulator state. This database records runner results after policy validation:

- tenant, client, and engagement records;
- signed job envelopes for allowed simulator runs;
- hashed fixture evidence;
- audit events for both denied and completed runs;
- a migration table and report draft table skeleton.

The storage layer is deliberately passive. It does not authorize jobs, execute adapters, or override runner decisions.

## Security Notes

- The UI is not a trusted authorization boundary; the runner re-validates each signed job envelope.
- Job signing keys are generated in memory for the local simulator and are not logged.
- Evidence content is deterministic fixture data and is hashed before report inclusion.
- Persistent audit records are local simulator artifacts and should not contain secrets.
- Reports are drafts and must not be represented as compliance certification.

## Roadmap

Phase P0 should continue by adding durable tenant/client/engagement storage, migrations, MCP planning/reporting resources that remain non-executing, broader schema documentation, CI dependency review, and an SBOM workflow. A2/A3 live capabilities remain out of scope until P0 acceptance criteria pass.
