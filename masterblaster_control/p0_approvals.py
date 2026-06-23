from __future__ import annotations

import uuid
from dataclasses import replace
from datetime import datetime, timedelta, timezone

from .p0_models import ApprovalRequest, Engagement
from .p0_policy import (
    REASON_ALLOW,
    REASON_APPROVAL_EXPIRED,
    REASON_APPROVAL_MISMATCH,
    REASON_APPROVAL_NOT_APPROVED,
    REASON_APPROVAL_REQUIRED,
    PolicyDecision,
    TargetParseError,
    parse_target,
)

APPROVAL_REASON_APPROVED = "APPROVED_FOR_P0_SIMULATION"
APPROVAL_REASON_DENIED = "DENIED_BY_HUMAN_REVIEW"
APPROVAL_REASON_EXPIRED = "EXPIRED_BEFORE_RUNNER_VALIDATION"


def _now(now: datetime | None = None) -> datetime:
    value = now or datetime.now(timezone.utc)
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value


def request_approval(
    engagement: Engagement,
    adapter_id: str,
    target: str,
    requested_by: str = "local-operator",
    now: datetime | None = None,
    ttl_seconds: int = 300,
) -> ApprovalRequest:
    current_time = _now(now)
    return ApprovalRequest(
        approval_id=f"approval-{uuid.uuid4()}",
        tenant_id=engagement.tenant_id,
        client_id=engagement.client_id,
        engagement_id=engagement.engagement_id,
        adapter_id=adapter_id,
        target=target,
        requested_by=requested_by,
        requested_at=current_time,
        expires_at=current_time + timedelta(seconds=ttl_seconds),
    )


def approve_request(
    approval: ApprovalRequest,
    decided_by: str = "local-human-approver",
    now: datetime | None = None,
) -> ApprovalRequest:
    current_time = _now(now)
    state = "expired" if approval.expires_at <= current_time else "approved"
    reason = APPROVAL_REASON_EXPIRED if state == "expired" else APPROVAL_REASON_APPROVED
    return replace(
        approval,
        state=state,
        decided_by=decided_by,
        decided_at=current_time,
        decision_reason=reason,
    )


def deny_request(
    approval: ApprovalRequest,
    decided_by: str = "local-human-approver",
    now: datetime | None = None,
) -> ApprovalRequest:
    return replace(
        approval,
        state="denied",
        decided_by=decided_by,
        decided_at=_now(now),
        decision_reason=APPROVAL_REASON_DENIED,
    )


def expire_request(approval: ApprovalRequest, now: datetime | None = None) -> ApprovalRequest:
    return replace(
        approval,
        state="expired",
        decided_at=_now(now),
        decision_reason=APPROVAL_REASON_EXPIRED,
    )


def validate_approval(
    approval: ApprovalRequest | None,
    engagement: Engagement,
    adapter_id: str,
    target: str,
    now: datetime | None = None,
) -> PolicyDecision:
    if approval is None:
        return PolicyDecision(False, REASON_APPROVAL_REQUIRED, "Human approval is required before job issue.")

    current_time = _now(now)
    try:
        _, normalized_target, _ = parse_target(target)
        _, normalized_approval_target, _ = parse_target(approval.target)
    except TargetParseError as exc:
        return PolicyDecision(False, REASON_APPROVAL_MISMATCH, f"Approval target could not be parsed: {exc}.")

    if approval.expires_at <= current_time:
        return PolicyDecision(False, REASON_APPROVAL_EXPIRED, "Human approval has expired.", normalized_target)

    if approval.state != "approved":
        return PolicyDecision(
            False,
            REASON_APPROVAL_NOT_APPROVED,
            f"Human approval is '{approval.state}', not approved.",
            normalized_target,
        )

    mismatches = []
    if approval.tenant_id != engagement.tenant_id:
        mismatches.append("tenant")
    if approval.client_id != engagement.client_id:
        mismatches.append("client")
    if approval.engagement_id != engagement.engagement_id:
        mismatches.append("engagement")
    if approval.adapter_id != adapter_id:
        mismatches.append("adapter")
    if normalized_approval_target != normalized_target:
        mismatches.append("target")

    if mismatches:
        return PolicyDecision(
            False,
            REASON_APPROVAL_MISMATCH,
            f"Human approval is not bound to the requested {', '.join(mismatches)}.",
            normalized_target,
        )

    return PolicyDecision(True, REASON_ALLOW, "Human approval validated.", normalized_target)
