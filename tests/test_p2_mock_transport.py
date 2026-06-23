from datetime import datetime, timezone

import pytest

from masterblaster_control.p0_approvals import approve_request, request_approval
from masterblaster_control.p0_policy import REASON_RATE_LIMIT
from masterblaster_control.p2_mock_transport import MockTransport, RateLimitState
from masterblaster_control.runner_simulator import RunnerSimulator, build_default_engagement


def test_mock_transport_serves_port_scan_fixture():
    transport = MockTransport()
    payload = transport.fetch("a5.port.scan_sim", "example.com")
    assert payload["transport"] == "mock"
    assert any(item["id"] == "port.open" for item in payload["observations"])


def test_rate_limit_denies_excess_requests():
    transport = MockTransport(rate_limit=RateLimitState(max_requests_per_minute=2))
    now = datetime(2026, 1, 1, tzinfo=timezone.utc)
    transport.fetch("a5.port.scan_sim", "example.com", now=now)
    transport.fetch("a5.port.scan_sim", "example.com", now=now)
    with pytest.raises(Exception):
        transport.fetch("a5.port.scan_sim", "example.com", now=now)


def test_runner_denies_when_rate_limit_exceeded():
    now = datetime(2026, 1, 1, tzinfo=timezone.utc)
    transport = MockTransport(rate_limit=RateLimitState(max_requests_per_minute=1))
    runner = RunnerSimulator(signing_key=bytes(range(32)), mock_transport=transport)
    engagement = build_default_engagement("example.com", now=now)
    approval = approve_request(
        request_approval(engagement, "a5.port.scan_sim", "example.com", now=now),
        now=now,
    )
    runner.run("a5.port.scan_sim", "example.com", engagement=engagement, approval=approval, now=now)
    second = runner.run("a5.port.scan_sim", "example.com", engagement=engagement, approval=approval, now=now)
    assert second.status == "denied"
    assert second.decision.reason_code == REASON_RATE_LIMIT