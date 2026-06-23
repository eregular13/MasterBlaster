# P0 Storage Skeleton

## Purpose

The P0 SQLite store records simulator state after the runner validates a policy decision and signed job envelope. It exists for auditability, UI continuity, and report draft assembly.

## Boundary

Storage is not an authorization boundary. The UI may request a run, but the `RunnerSimulator` evaluates policy and validates envelopes before the storage layer receives a result.

## Current Tables

- `schema_migrations`: local migration version tracking.
- `tenants`: simulator tenant records.
- `clients`: simulator client records.
- `engagements`: authorized scope and rules-of-engagement snapshots.
- `jobs`: signed simulator job envelopes and policy decisions.
- `evidence_records`: deterministic fixture evidence with parser and hash provenance.
- `audit_events`: completed and denied runner outcomes.
- `report_drafts`: reserved skeleton for draft report metadata.

## Migration Rule

Schema updates must be append-only migrations with tests. Migrations must not introduce live execution, network transport, secrets, or policy bypasses.

## P0 Limitation

The default desktop database is local-only at `data/masterblaster_p0.sqlite3`. Durable multi-user tenancy, authn/authz, retention policy, and encrypted-at-rest configuration are future acceptance items.
