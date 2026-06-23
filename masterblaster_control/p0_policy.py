from __future__ import annotations

import hmac
import ipaddress
import json
import re
from dataclasses import replace
from datetime import datetime, timedelta, timezone
from hashlib import sha256
from typing import Any, Mapping
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
REASON_APPROVAL_REPLAY = "DENY_APPROVAL_REPLAY"
REASON_JOB_APPROVAL_MISSING = "DENY_JOB_APPROVAL_MISSING"
REASON_JOB_TENANT_MISMATCH = "DENY_JOB_TENANT_MISMATCH"
REASON_JOB_CLIENT_MISMATCH = "DENY_JOB_CLIENT_MISMATCH"
REASON_JOB_ENGAGEMENT_MISMATCH = "DENY_JOB_ENGAGEMENT_MISMATCH"
REASON_JOB_ADAPTER_MISMATCH = "DENY_JOB_ADAPTER_MISMATCH"
REASON_JOB_TARGET_MISMATCH = "DENY_JOB_TARGET_MISMATCH"
REASON_JOB_ARGUMENT_TARGET_MISMATCH = "DENY_JOB_ARGUMENT_TARGET_MISMATCH"
REASON_JOB_TIME_WINDOW = "DENY_JOB_TIME_WINDOW"
REASON_JOB_ISSUED_IN_FUTURE = "DENY_JOB_ISSUED_IN_FUTURE"
REASON_JOB_TTL_EXCEEDED = "DENY_JOB_TTL_EXCEEDED"

MAX_JOB_FUTURE_SKEW_SECONDS = 30

_DOMAIN_RE = re.compile(r"^(?=.{1,253}$)([a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z]{2,63}$")
_HOST_RE = re.compile(r"^[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?$")


class TargetParseError(ValueError):
    pass


def _now(now: datetime | None = None) -> datetime:
    value = now or datetime.now(timezone.utc)
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value


def canonical_json(data: Any) -> str:
    return json.dumps(data, sort_keys=True, separators=(",", ":"), default=str)


def parse_target(raw: str) -> tuple[str, str, str | None]:
    if not isinstance(raw, str):
        raise TargetParseError("target must be a string")
    value = raw.strip().lower()
    if not value or any(ch.isspace() for ch in value):
        raise TargetParseError("target must be a single host, domain, URL, IP, or CIDR")
    if any(ord(ch) < 32 or ord(ch) == 127 for ch in value):
        raise TargetParseError("target must not include control characters")
    try:
        value.encode("ascii")
    except UnicodeEncodeError as exc:
        raise TargetParseError("target must use unambiguous ASCII characters") from exc

    try:
        parsed = urlparse(value)
    except ValueError as exc:
        raise TargetParseError("target URL structure is invalid") from exc
    if parsed.scheme:
        try:
            parsed_hostname = parsed.hostname
            parsed_port = parsed.port
        except ValueError as exc:
            raise TargetParseError("target URL structure is invalid") from exc
        if parsed.scheme not in {"http", "https"} or not parsed_hostname:
            raise TargetParseError("only http and https URLs with hostnames are accepted")
        if parsed.username or parsed.password:
            raise TargetParseError("URL targets must not include userinfo or credentials")
        if parsed.query or parsed.fragment:
            raise TargetParseError("URL targets must not include query strings or fragments")
        if "%" in parsed.netloc:
            raise TargetParseError("URL host must not use percent-encoded ambiguity")
        host = parsed_hostname.lower()
        port = f":{parsed_port}" if parsed_port else ""
        path = parsed.path or "/"
        if "%" in host or "%" in path:
            raise TargetParseError("URL target must not use percent-encoded ambiguity")
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
    if not job.approval_id:
        return PolicyDecision(False, REASON_JOB_APPROVAL_MISSING, "Job is not bound to a human approval ID.")
    if job.issued_at > current_time + timedelta(seconds=MAX_JOB_FUTURE_SKEW_SECONDS):
        return PolicyDecision(False, REASON_JOB_ISSUED_IN_FUTURE, "Job was issued too far in the future.")
    if job.expires_at <= job.issued_at:
        return PolicyDecision(False, REASON_JOB_TIME_WINDOW, "Job expiry must be after issued-at.")
    ttl_seconds = int((job.expires_at - job.issued_at).total_seconds())
    if ttl_seconds <= 0 or ttl_seconds > engagement.rules.max_runtime_seconds:
        return PolicyDecision(False, REASON_JOB_TTL_EXCEEDED, "Job TTL exceeds the rules of engagement bound.")
    if job.expires_at <= current_time:
        return PolicyDecision(False, REASON_EXPIRED_JOB, "Job envelope has expired.")
    if job.tenant_id != engagement.tenant_id:
        return PolicyDecision(False, REASON_JOB_TENANT_MISMATCH, "Job tenant does not match engagement tenant.")
    if job.client_id != engagement.client_id:
        return PolicyDecision(False, REASON_JOB_CLIENT_MISMATCH, "Job client does not match engagement client.")
    if job.engagement_id != engagement.engagement_id:
        return PolicyDecision(False, REASON_JOB_ENGAGEMENT_MISMATCH, "Job is not bound to this engagement.")
    if manifest and job.adapter_id != manifest.adapter_id:
        return PolicyDecision(False, REASON_JOB_ADAPTER_MISMATCH, "Job adapter does not match manifest.")
    try:
        _, normalized_job_target, _ = parse_target(job.target)
    except TargetParseError as exc:
        return PolicyDecision(False, REASON_INVALID_TARGET, str(exc))
    if normalized_job_target != job.target:
        return PolicyDecision(False, REASON_JOB_TARGET_MISMATCH, "Job target is not in canonical normalized form.")
    argument_target = job.arguments.get("target")
    if argument_target is not None:
        try:
            _, normalized_argument_target, _ = parse_target(argument_target)
        except TargetParseError as exc:
            return PolicyDecision(False, REASON_INVALID_TARGET, f"Job target argument is invalid: {exc}.")
        if normalized_argument_target != job.target:
            return PolicyDecision(
                False,
                REASON_JOB_ARGUMENT_TARGET_MISMATCH,
                "Job target argument does not match the signed target binding.",
                job.target,
            )
    return evaluate_policy(manifest, engagement, job.target, job.arguments, now=current_time)
