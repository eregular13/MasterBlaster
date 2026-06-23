# P0 Read-Only MCP Facade

## Purpose

`masterblaster_control/p0_mcp_readonly.py` provides a dependency-free MCP-shaped facade for resources and draft-only tools. It is the safe core that a future MCP transport can wrap.

## Exposed Capabilities

- list registered P0 resource descriptors;
- read a registered P0 resource;
- list read-only tool descriptors;
- render a planning brief;
- render a report draft from local storage counts and explicit tenant-scoped summaries.

## Non-Capabilities

The facade does not expose:

- job execution;
- adapter invocation;
- network transport;
- shell commands;
- approval mutation;
- policy overrides;
- target contact.

Unknown tool names fail closed with `UnknownReadOnlyToolError`. Draft tools are rendered with `render_tool(...)`; the facade does not expose a generic command or adapter execution API. Without an explicit tenant scope, report drafts intentionally omit stored audit/evidence rows instead of falling back to a global query.

## Safety Boundary

The facade is not a trusted authorization boundary. It reads deterministic resources and local storage summaries only. Constructing the facade without storage uses an empty read-only view and does not create or migrate a database. Any future MCP server must delegate to this facade and must not add runnable tools until P0 acceptance gates are complete.

## Regression Coverage

`tests/test_p0_mcp_readonly.py` verifies that:

- descriptors are marked non-executing;
- unknown read-only tool names fail closed;
- generated drafts retain simulator-only disclaimers;
- rendering with default storage does not create a database file;
- generated timestamps can be injected for deterministic tests;
- the facade does not import `RunnerSimulator` or `runner_simulator`.
