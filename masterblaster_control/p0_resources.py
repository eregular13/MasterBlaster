from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Literal

from .p0_acceptance import acceptance_dashboard_markdown

ResourceCategory = Literal["planning", "reporting", "governance"]


class UnknownResourceError(KeyError):
    pass


@dataclass(frozen=True)
class P0Resource:
    uri: str
    title: str
    category: ResourceCategory
    version: str
    content_type: str
    summary: str
    body: str
    non_executing: bool = True

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


_RESOURCES: tuple[P0Resource, ...] = (
    P0Resource(
        uri="p0://planning/engagement-template",
        title="Engagement Setup Template",
        category="planning",
        version="0.1.0",
        content_type="text/markdown",
        summary="Template for tenant, client, engagement, authorization, scope, and expiry planning.",
        body="""# Engagement Setup Template

This resource is non-executing. It cannot create jobs, launch adapters, contact targets, or approve work.

## Required Fields

- Tenant ID:
- Client ID:
- Engagement ID:
- Engagement owner:
- Authorization source:
- Authorized target patterns:
- Start time:
- Expiration time:
- Rules-of-engagement summary:
- Required human approval checkpoint:

## P0 Validation Notes

- Unknown targets default to deny.
- Expired engagements default to deny.
- UI-entered values must be re-validated by the runner before evidence is emitted.
""",
    ),
    P0Resource(
        uri="p0://planning/rules-of-engagement-template",
        title="Rules Of Engagement Template",
        category="planning",
        version="0.1.0",
        content_type="text/markdown",
        summary="Template for P0-safe rules-of-engagement constraints.",
        body="""# Rules Of Engagement Template

This resource is non-executing. It describes policy input only.

## P0 Constraints

- Network transport allowed: false
- Live tool execution allowed: false
- Fixture-only evidence: true
- Maximum simulator job runtime seconds:
- Authorized adapter IDs:
- Authorized target patterns:
- Evidence retention expectation:
- Report disclaimer required: true

## Fail-Closed Requirements

- Unknown adapter -> deny.
- Unknown argument -> deny.
- Unknown target type -> deny.
- Expired job envelope -> deny.
- Invalid signature -> deny.
""",
    ),
    P0Resource(
        uri="p0://planning/workflow-template",
        title="Simulator Workflow Template",
        category="planning",
        version="0.1.0",
        content_type="text/markdown",
        summary="Template for ordering reviewed simulator adapters without granting execution authority.",
        body="""# Simulator Workflow Template

This resource is non-executing. Workflow order is advisory until each adapter request passes runner validation.

## Suggested P0 Flow

1. Confirm engagement authorization and expiry.
2. Validate target is in scope.
3. Run `a0.fixture.inventory`.
4. Run `a1.tls.assessment` when target type is domain or URL.
5. Review evidence hashes and parser provenance.
6. Export report draft with simulator-only disclaimer.

## Runner Rule

Each step must create a signed, expiring job envelope and must be independently validated.
""",
    ),
    P0Resource(
        uri="p0://reporting/report-draft-outline",
        title="Report Draft Outline",
        category="reporting",
        version="0.1.0",
        content_type="text/markdown",
        summary="Non-compliance-reporting outline for simulator evidence and audit history.",
        body="""# Report Draft Outline

This resource is non-executing and does not certify compliance or security.

## Sections

1. Engagement context
2. Scope and authorization summary
3. Rules-of-engagement summary
4. Simulator adapter inventory
5. Evidence hash table
6. Parser and adapter provenance
7. Audit event timeline
8. Findings requiring human review
9. Limitations and draft disclaimer

## Required Disclaimer

This report is a simulator draft only. It is not a compliance attestation, certification, or proof of security.
""",
    ),
    P0Resource(
        uri="p0://governance/acceptance-checklist",
        title="P0 Acceptance Checklist",
        category="governance",
        version="0.1.0",
        content_type="text/markdown",
        summary="Acceptance controls required before any A2/A3 live capability discussion.",
        body=(
            "This resource is non-executing. It is governance telemetry only and cannot approve, "
            "create, or run jobs.\n\n"
            + acceptance_dashboard_markdown()
        ),
    ),
)

_RESOURCE_BY_URI = {resource.uri: resource for resource in _RESOURCES}


def list_resources(category: ResourceCategory | None = None) -> tuple[P0Resource, ...]:
    if category is None:
        return _RESOURCES
    return tuple(resource for resource in _RESOURCES if resource.category == category)


def read_resource(uri: str) -> P0Resource:
    try:
        return _RESOURCE_BY_URI[uri]
    except KeyError as exc:
        raise UnknownResourceError(f"Unknown P0 resource URI: {uri}") from exc


def resource_summary_markdown() -> str:
    lines = ["# Non-Executing P0 Resources", ""]
    for resource in _RESOURCES:
        lines.extend(
            [
                f"## {resource.title}",
                "",
                f"- URI: `{resource.uri}`",
                f"- Category: `{resource.category}`",
                f"- Version: `{resource.version}`",
                f"- Non-executing: `{resource.non_executing}`",
                f"- Summary: {resource.summary}",
                "",
            ]
        )
    return "\n".join(lines).strip()
