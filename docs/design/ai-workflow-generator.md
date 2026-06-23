# AI Workflow Generator Specification (P7)

## Purpose

Generate **non-executing** engagement workflow drafts from scope, adapter catalog, and policy constraints.

## Inputs

- Engagement scope targets
- Available reviewed adapter manifests
- Rules of engagement (no network, max runtime)
- Historical audit/evidence summaries (read-only)

## Outputs

- Ordered adapter workflow draft (JSON + Markdown)
- Human approval checklist per step
- Explicit disclaimer: draft only, not auto-executed

## Constraints

- Must not bypass human approval gate
- Must not invoke runner directly
- Must not claim compliance or certification
- Must cite adapter IDs from reviewed registry only

## API Shape (future)

```python
generate_workflow_draft(
    engagement_id: str,
    objectives: list[str],
) -> WorkflowDraft
```

## Evaluation

- Deterministic fallback templates when AI unavailable
- Snapshot tests for prompt output structure
- Red-team tests for policy bypass suggestions