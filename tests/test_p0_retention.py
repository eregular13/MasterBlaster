from datetime import datetime, timezone

import pytest

from masterblaster_control.p0_retention import REDACTION_MARKER, RetentionPolicy, redact_for_storage, retention_cutoff


def test_redaction_removes_sensitive_keys_recursively():
    payload = {
        "safe": "fixture",
        "api_key": "should-not-persist",
        "nested": {
            "password": "should-not-persist",
            "items": [{"token": "should-not-persist"}, {"name": "kept"}],
        },
    }

    redacted = redact_for_storage(payload)

    assert redacted["safe"] == "fixture"
    assert redacted["api_key"] == REDACTION_MARKER
    assert redacted["nested"]["password"] == REDACTION_MARKER
    assert redacted["nested"]["items"][0]["token"] == REDACTION_MARKER
    assert redacted["nested"]["items"][1]["name"] == "kept"


def test_redaction_removes_inline_secret_strings():
    assert redact_for_storage("token=abc123") == REDACTION_MARKER
    assert redact_for_storage("ordinary fixture observation") == "ordinary fixture observation"


def test_retention_policy_requires_positive_windows():
    with pytest.raises(ValueError):
        RetentionPolicy(audit_retention_days=0).validate()


def test_retention_cutoff_is_deterministic():
    now = datetime(2026, 1, 10, tzinfo=timezone.utc)

    assert retention_cutoff(5, now=now) == "2026-01-05T00:00:00+00:00"
