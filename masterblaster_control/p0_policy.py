from __future__ import annotations

import hmac
import ipaddress
import json
import re
from dataclasses import replace
from datetime import datetime, timezone
from hashlib import sha256
from typing import Mapping
from urllib.parse import urlparse

from .p0_models import AdapterManifest, Engagement, JobEnvelope, PolicyDecision, ScopeTarget

REASON_ALLOW = "ALLOW"
REASON_BAD_SIGNATURE = "DENY_BAD_SIGNATURE"
REASON_EXPIRED_ENGAGEMENT = "DENY_EXPIRED_ENGAGEMENT"
REASON_EXPIRED_JOB = "DENY_EXPIRED_JOB"
REASON_INVALID_TARGET = "DENY_INVALID_TARGET"
REASON_NETWORK_TRANSPORT = "DENY_NETWORK_TRANSPORT"
REASON_TARGET_OUT_OF_SCOPE = "DENY_TARGET_OUT_OF_SCOPE"
REASON_TARGET_TYPE = "DENY_TARGET_TYPE"
REASON_UNKNOWN_ADAPTER = "DENY_UNKNOWN_ADAPTER"
REASON_UNKNOWN_ARGUMENT = "DENY_UNKNOWN_ARGUMENT"
REASON_UNREVIEWED_ADAPTER = "DENY_UNREVIEWED_ADAPTER"
REASON_APPROVAL_REQUIRED = "DENY_APPROVAL_REQUIRED"
REASON_APPROVAL_NOT_APPROVED = "DENY_APPROVAL_NOT_APPROVED"
REASON_APPROVAL_EXPIRED = "DENY_APPROVAL_EXPIRED"
REASON_APPROVAL_MISMATCH = "DENY_APPROVAL_MISMATCH"
REASON_RATE_LIMIT = "DENY_RATE_LIMIT"

_DOMAIN_RE = re.compile(r"^(?=.{1,253}$)([a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z]{2,63}$")
_HOST_RE = re.compile(r"^[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?$")


class TargetParseError(ValueError):
    pass


def _now(now: datetime | None = None) -> datetime:
    value = now or datetime.now(timezone.utc)
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value


def canonical_json(data: Mapping[str, object]) -> str:
    return json.dumps(data, sort_keys=True, separators=(",", ":"), default=str)


def parse_target(raw: str) -> tuple[str, str, str | None]:
    value = (raw or "").strip().lower()
    if not value or any(ch.isspace() for ch in value):
        raise TargetParseError("target must be a single host, domain, URL, IP, or CIDR")

    parsed = urlparse(value)
    if parsed.scheme:
        if parsed.scheme not in {"http", "https"} or not parsed.hostname:
            raise TargetParseError("only http and https URLs with hostnames are accepted")
        host = parsed.hostname.lower()
        port = f":{parsed.port}" if parsed.port else ""
        path = parsed.path or "/"
        normalized = f"{parsed.scheme}://{host}{port}{path}"
        return "url", normalized, host

    try:
        network = ipaddress.ip_network(value, strict=False)
        if "/" in value:
            return "cidr", str(network), None
    except ValueError:
        network = None

    try:
        address = ipaddress.ip_address(value)
        return "ip", str(address), None
    except ValueError:
        pass

    if _DOMAIN_RE.match(value):
        return "domain", value, value
    if _HOST_RE.match(value):
        return "host", value, value
    raise TargetParseError("target did not match an allowed deterministic target form")


def _target_matches_scope(raw_target: str, scope: ScopeTarget) -> bool:
    target_type, target_value, target_host = parse_target(raw_target)
    scope_type, scope_value, scope_host = parse_target(scope.pattern)

    if target_value == scope_value:
        return True
    if scope_type == "cidr" and target_type == "ip":
        return ipaddress.ip_address(target_value) in ipaddress.ip_network(scope_value)
    if target_type == "url" and scope_type in {"domain", "host"}:
        return target_host == scope_host
    return False


def evaluate_policy(
    manifest: AdapterManifest | None,
    engagement: Engagement,
    target: str,
    arguments: Mapping[str, str] | None = None,
    now: datetime | None = None,
) -> PolicyDecision:
    if manifest is None:
        return PolicyDecision(False, REASON_UNKNOWN_ADAPTER, "Adapter is not registered.")
    if not manifest.reviewed:
        return PolicyDecision(False, REASON_UNREVIEWED_ADAPTER, "Adapter manifest has not been reviewed.")

    current_time = _now(now)
    if engagement.expires_at <= current_time:
        return PolicyDecision(False, REASON_EXPIRED_ENGAGEMENT, "Engagement authorization has expired.")

    arguments = arguments or {}
    unknown_args = sorted(set(arguments) - set(manifest.parameters))
    if unknown_args:
        return PolicyDecision(
            False,
            REASON_UNKNOWN_ARGUMENT,
            f"Unknown adapter argument(s): {', '.join(unknown_args)}.",
        )

    try:
        target_type, normalized_target, _ = parse_target(target)
    except TargetParseError as exc:
        return PolicyDecision(False, REASON_INVALID_TARGET, str(exc))

    if target_type not in manifest.allowed_target_types:
        return PolicyDecision(
            False,
            REASON_TARGET_TYPE,
            f"Adapter does not accept target type '{target_type}'.",
            normalized_target,
        )

    if manifest.network_access and not engagement.rules.allow_network_transport:
        return PolicyDecision(
            False,
            REASON_NETWORK_TRANSPORT,
            "Rules of engagement do not allow network transport.",
            normalized_target,
        )

    try:
        in_scope = any(_target_matches_scope(target, scope) for scope in engagement.authorized_targets)
    except TargetParseError as exc:
        return PolicyDecision(False, REASON_INVALID_TARGET, f"Invalid scope target: {exc}.", normalized_target)

    if not in_scope:
        return PolicyDecision(
            False,
            REASON_TARGET_OUT_OF_SCOPE,
            "Target is outside the engagement authorization.",
            normalized_target,
        )

    return PolicyDecision(True, REASON_ALLOW, "Policy allowed simulator job.", normalized_target)


def sign_job_envelope(job: JobEnvelope, signing_key: bytes) -> JobEnvelope:
    payload = canonical_json(job.to_dict(include_signature=False)).encode("utf-8")
    signature = hmac.new(signing_key, payload, sha256).hexdigest()
    return replace(job, signature=signature)


def verify_job_signature(job: JobEnvelope, signing_key: bytes) -> bool:
    expected = sign_job_envelope(job.unsigned(), signing_key).signature
    return hmac.compare_digest(expected, job.signature)


def validate_job_envelope(
    job: JobEnvelope,
    manifest: AdapterManifest | None,
    engagement: Engagement,
    signing_key: bytes,
    now: datetime | None = None,
) -> PolicyDecision:
    current_time = _now(now)
    if not verify_job_signature(job, signing_key):
        return PolicyDecision(False, REASON_BAD_SIGNATURE, "Job signature did not verify.")
    if job.expires_at <= current_time:
        return PolicyDecision(False, REASON_EXPIRED_JOB, "Job envelope has expired.")
    if job.engagement_id != engagement.engagement_id:
        return PolicyDecision(False, REASON_TARGET_OUT_OF_SCOPE, "Job is not bound to this engagement.")
    if manifest and job.adapter_id != manifest.adapter_id:
        return PolicyDecision(False, REASON_UNKNOWN_ADAPTER, "Job adapter does not match manifest.")
    return evaluate_policy(manifest, engagement, job.target, job.arguments, now=current_time)
