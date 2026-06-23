from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass
class RateLimitState:
    max_requests_per_minute: int = 30
    window_seconds: int = 60
    _events: list[datetime] = field(default_factory=list)

    def check(self, now: datetime | None = None) -> tuple[bool, str]:
        current = now or datetime.now(timezone.utc)
        if current.tzinfo is None:
            current = current.replace(tzinfo=timezone.utc)
        cutoff = current.timestamp() - self.window_seconds
        self._events = [event for event in self._events if event.timestamp() >= cutoff]
        if len(self._events) >= self.max_requests_per_minute:
            return False, "DENY_RATE_LIMIT"
        self._events.append(current)
        return True, "ALLOW"


class MockTransport:
    """P2 safe simulation transport — fixture responses only, no sockets."""

    def __init__(self, rate_limit: RateLimitState | None = None):
        self.rate_limit = rate_limit or RateLimitState()

    def fetch(self, adapter_id: str, target: str, now: datetime | None = None) -> dict[str, Any]:
        allowed, reason = self.rate_limit.check(now=now)
        if not allowed:
            raise MockTransportDenied(reason)

        if adapter_id == "a5.port.scan_sim":
            return {
                "transport": "mock",
                "target": target,
                "observations": [
                    {"id": "port.open", "value": [22, 80, 443]},
                    {"id": "port.filtered", "value": [3306]},
                    {"id": "scan.rate_limited", "value": True},
                ],
            }
        if adapter_id == "a6.web.crawl_sim":
            return {
                "transport": "mock",
                "target": target,
                "observations": [
                    {"id": "crawl.pages", "value": 12},
                    {"id": "crawl.forms", "value": 2},
                    {"id": "crawl.external_links", "value": 5},
                ],
            }
        if adapter_id in {"a1.tls.assessment", "a4.tls.cert_expiry"}:
            return {
                "transport": "mock",
                "target": target,
                "observations": [{"id": "tls.mock", "value": "fixture-handshake"}],
            }
        return {
            "transport": "mock",
            "target": target,
            "observations": [{"id": "mock.generic", "value": "fixture-response"}],
        }


class MockTransportDenied(RuntimeError):
    def __init__(self, reason_code: str):
        super().__init__(reason_code)
        self.reason_code = reason_code