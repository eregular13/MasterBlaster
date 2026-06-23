# P0 Retention And Redaction Controls

## Purpose

P0 storage must preserve simulator auditability without becoming an unbounded or secret-bearing local artifact store.

## Redaction Boundary

`masterblaster_control/p0_retention.py` recursively redacts JSON values before persistence when keys or inline string patterns look secret-bearing.

Examples of redacted keys include:

- `api_key`
- `access_key`
- `password`
- `private_key`
- `secret`
- `token`
- `credential`

Redaction is defensive only. Operators must still avoid placing secrets in prompts, logs, job payloads, fixtures, reports, or local storage.

## Retention Boundary

`P0Storage.apply_retention()` purges:

- evidence records;
- jobs;
- approvals;
- audit events.

Tenants, clients, and engagements are retained by default because they represent simulator authorization context and will need explicit lifecycle ownership in a future management UI.

## Safety Property

Retention is ordered to avoid breaking SQLite foreign-key constraints:

1. evidence records;
2. jobs;
3. unreferenced approvals;
4. audit events.

No retention operation launches tools, touches networks, or changes policy decisions.
