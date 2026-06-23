# P0 Non-Executing Resources

## Purpose

P0 resources provide planning, reporting, and governance templates that can be exposed by a future MCP server without granting execution authority.

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

## Future MCP Wrapper

A future MCP service may expose these records as resources. That service must preserve the same boundary: resource reads are allowed, job execution is not. Any planning or reporting tool must produce drafts only and must never issue runnable jobs until approval and runner policy are complete.
