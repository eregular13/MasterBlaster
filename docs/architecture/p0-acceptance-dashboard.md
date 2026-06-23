# P0 Acceptance Dashboard

## Purpose

The acceptance dashboard turns P0 readiness into deterministic, reviewable data. It links each criterion to implementation evidence and next actions so unfinished work cannot hide behind optimistic prose.

## Boundary

The dashboard is governance telemetry only. It cannot approve engagements, execute adapters, write policy decisions, create signed jobs, or certify compliance.

## Source Of Truth

`masterblaster_control/p0_acceptance.py` owns the frozen criteria registry. The Qt Guardrails panel, report draft exports, validator script, and `docs/P0_ACCEPTANCE_CHECKLIST.md` consume that registry.

## Percent Semantics

- `100%`: implemented and covered by evidence links.
- `1-99%`: partially implemented; the next action explains the missing work.
- `0%`: not started and should block P1 if marked as a P1 gate.

## Current Readiness

The current dashboard separates broad reference-grade completion from P1 gating completion. This prevents the project from claiming readiness while human approval, MCP wrapping, CI/SBOM, review policy, or retention controls remain unfinished.
