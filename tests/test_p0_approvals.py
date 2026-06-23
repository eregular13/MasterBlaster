from dataclasses import replace
from datetime import datetime, timedelta, timezone

from masterblaster_control.p0_approvals import (
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
