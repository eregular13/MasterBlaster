from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, Mapping

REDACTION_MARKER = "[REDACTED]"

SENSITIVE_KEY_FRAGMENTS = (
    "api_key",
    "apikey",
    "access_key",
    "auth",
    "credential",
    "password",
    "private_key",
    "secret",
    "token",
)

INLINE_SECRET_PATTERN = re.compile(
    r"(api[_-]?key|access[_-]?key|password|secret|token|credential)\s*[:=]\s*\S+",
    flags=re.IGNORECASE,
)


@dataclass(frozen=True)
class RetentionPolicy:
    audit_retention_days: int = 30
    evidence_retention_days: int = 30
    job_retention_days: int = 30
    approval_retention_days: int = 30

    def validate(self) -> None:
        for field_name, value in (
            ("audit_retention_days", self.audit_retention_days),
            ("evidence_retention_days", self.evidence_retention_days),
            ("job_retention_days", self.job_retention_days),
            ("approval_retention_days", self.approval_retention_days),
        ):
            if value < 1:
                raise ValueError(f"{field_name} must be at least 1 day")


@dataclass(frozen=True)
class RetentionResult:
    approvals_deleted: int
    jobs_deleted: int
    evidence_deleted: int
    audit_events_deleted: int


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def retention_cutoff(days: int, now: datetime | None = None) -> str:
    current_time = now or utc_now()
    if current_time.tzinfo is None:
        current_time = current_time.replace(tzinfo=timezone.utc)
    return (current_time - timedelta(days=days)).isoformat()


def redact_for_storage(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {
            str(key): REDACTION_MARKER if _is_sensitive_key(str(key)) else redact_for_storage(item)
            for key, item in value.items()
        }
    if isinstance(value, (list, tuple)):
        return [redact_for_storage(item) for item in value]
    if isinstance(value, str) and INLINE_SECRET_PATTERN.search(value):
        return REDACTION_MARKER
    return value


def _is_sensitive_key(key: str) -> bool:
    normalized = key.lower().replace("-", "_")
    return any(fragment in normalized for fragment in SENSITIVE_KEY_FRAGMENTS)
