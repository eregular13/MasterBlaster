from dataclasses import replace
from datetime import datetime, timedelta, timezone

import pytest

from masterblaster_control.p0_approvals import (
    ApprovalTransitionError,
    approve_request,
    deny_request,
    request_approval,
    validate_approval,
)
from masterblaster_control.p0_policy import (
    REASON_ALLOW,
    REASON_APPROVAL_EXPIRED,
    REASON_APPROVAL_MISMATCH,
    REASON_APPROVAL_NOT_APPROVED,
)
from masterblaster_control.runner_simulator import build_default_engagement


def test_approved_request_validates_against_matching_runner_context():
    now = datetime(2026, 1, 1, tzinfo=timezone.utc)
    engagement = build_default_engagement("example.com", now=now)
    approval = request_approval(engagement, "a0.fixture.inventory", "example.com", now=now)
    approved = approve_request(approval, now=now)

    decision = validate_approval(approved, engagement, "a0.fixture.inventory", "example.com", now=now)

    assert approved.state == "approved"
    assert decision.allowed is True
    assert decision.reason_code == REASON_ALLOW


def test_denied_request_fails_runner_validation():
    now = datetime(2026, 1, 1, tzinfo=timezone.utc)
    engagement = build_default_engagement("example.com", now=now)
    approval = deny_request(request_approval(engagement, "a0.fixture.inventory", "example.com", now=now), now=now)

    decision = validate_approval(approval, engagement, "a0.fixture.inventory", "example.com", now=now)

    assert decision.allowed is False
    assert decision.reason_code == REASON_APPROVAL_NOT_APPROVED


def test_expired_request_fails_runner_validation_even_if_previously_approved():
    now = datetime(2026, 1, 1, tzinfo=timezone.utc)
    engagement = build_default_engagement("example.com", now=now)
    approval = request_approval(engagement, "a0.fixture.inventory", "example.com", now=now, ttl_seconds=1)
    approved = approve_request(approval, now=now)

    decision = validate_approval(
        approved,
        engagement,
        "a0.fixture.inventory",
        "example.com",
        now=now + timedelta(seconds=2),
    )

    assert decision.allowed is False
    assert decision.reason_code == REASON_APPROVAL_EXPIRED


def test_approval_bound_to_different_adapter_or_target_fails_closed():
    now = datetime(2026, 1, 1, tzinfo=timezone.utc)
    engagement = build_default_engagement("example.com", now=now)
    approval = approve_request(
        request_approval(engagement, "a0.fixture.inventory", "example.com", now=now),
        now=now,
    )
    mismatched = replace(approval, adapter_id="a1.tls.assessment")

    decision = validate_approval(mismatched, engagement, "a0.fixture.inventory", "example.com", now=now)

    assert decision.allowed is False
    assert decision.reason_code == REASON_APPROVAL_MISMATCH


def test_approval_state_machine_rejects_repeated_or_conflicted_decisions():
    now = datetime(2026, 1, 1, tzinfo=timezone.utc)
    engagement = build_default_engagement("example.com", now=now)
    approval = request_approval(engagement, "a0.fixture.inventory", "example.com", now=now)
    approved = approve_request(approval, now=now)

    with pytest.raises(ApprovalTransitionError, match="already approved"):
        approve_request(approved, now=now)
    with pytest.raises(ApprovalTransitionError, match="already approved"):
        deny_request(approved, now=now)


def test_approval_requires_distinct_requester_and_approver():
    now = datetime(2026, 1, 1, tzinfo=timezone.utc)
    engagement = build_default_engagement("example.com", now=now)
    approval = request_approval(
        engagement,
        "a0.fixture.inventory",
        "example.com",
        requested_by="same-user",
        now=now,
    )

    with pytest.raises(ApprovalTransitionError, match="distinct"):
        approve_request(approval, decided_by="same-user", now=now)


def test_structurally_invalid_approval_fails_closed():
    now = datetime(2026, 1, 1, tzinfo=timezone.utc)
    engagement = build_default_engagement("example.com", now=now)
    approval = request_approval(engagement, "a0.fixture.inventory", "example.com", now=now)
    invalid = replace(approval, requested_by="")

    decision = validate_approval(invalid, engagement, "a0.fixture.inventory", "example.com", now=now)

    assert decision.allowed is False
    assert decision.reason_code == REASON_APPROVAL_MISMATCH
