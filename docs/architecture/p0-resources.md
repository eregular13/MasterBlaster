# P0 Non-Executing Resources

## Purpose

P0 resources provide planning, reporting, and governance templates that can be exposed through the read-only MCP facade without granting execution authority.

## Boundary

Resources are inert content. They cannot approve engagements, create trusted authorization state, run adapters, contact targets, read secrets, or override the runner.

## Current Registry

The closed registry lives in `masterblaster_control/p0_resources.py` and includes:

- `p0://planning/engagement-template`
- `p0://planning/rules-of-engagement-template`
- `p0://planning/workflow-template`
- `p0://reporting/report-draft-outline`
- `p0://governance/acceptance-checklist`

Unknown resource URIs fail closed with `UnknownResourceError`.

## Read-Only MCP Facade

`masterblaster_control/p0_mcp_readonly.py` exposes these records as resource descriptors and supports draft-only renderers for planning briefs and report drafts. The facade preserves the same boundary: resource reads are allowed, job execution is not. Any future transport wrapper must delegate to this facade and must not add runnable tools until approval and runner policy are complete.
