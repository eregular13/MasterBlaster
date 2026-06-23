from __future__ import annotations

import secrets
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from hashlib import sha256
from types import MappingProxyType
from typing import Any, Mapping

from .p0_approvals import validate_approval
from .p0_models import (
    AdapterManifest,
    ApprovalRequest,
    Engagement,
    EvidenceRecord,
    JobEnvelope,
    PolicyDecision,
    RulesOfEngagement,
    ScopeTarget,
)
from .p0_policy import (
    REASON_ALLOW,
    REASON_RATE_LIMIT,
    canonical_json,
    evaluate_policy,
    sign_job_envelope,
    validate_job_envelope,
)
from .mcp_catalog import MCP_CATALOG_ORDER, build_mcp_catalog
from .p2_mock_transport import MockTransport, MockTransportDenied

_MANIFESTS: dict[str, AdapterManifest] = build_mcp_catalog()

MANIFESTS: Mapping[str, AdapterManifest] = MappingProxyType(_MANIFESTS)
MCP_COUNT = len(MCP_CATALOG_ORDER)


@dataclass(frozen=True)
class RunnerResult:
    status: str
    decision: PolicyDecision
    engagement: Engagement
    approval: ApprovalRequest | None = None
    job: JobEnvelope | None = None
    evidence: tuple[EvidenceRecord, ...] = ()


def build_default_engagement(target: str, now: datetime | None = None) -> Engagement:
    current_time = now or datetime.now(timezone.utc)
    if current_time.tzinfo is None:
        current_time = current_time.replace(tzinfo=timezone.utc)
    return Engagement(
        engagement_id="engagement-local-simulator",
        tenant_id="tenant-local-simulator",
        client_id="client-local-simulator",
        authorized_targets=(ScopeTarget(pattern=target),),
        rules=RulesOfEngagement(allow_network_transport=False, max_runtime_seconds=30),
        expires_at=current_time + timedelta(minutes=15),
    )


class RunnerSimulator:
    def __init__(self, signing_key: bytes | None = None, mock_transport: MockTransport | None = None):
        self._signing_key = signing_key or secrets.token_bytes(32)
        self._mock_transport = mock_transport or MockTransport()

    def run(
        self,
        adapter_id: str,
        target: str,
        engagement: Engagement | None = None,
        approval: ApprovalRequest | None = None,
        arguments: Mapping[str, str] | None = None,
        now: datetime | None = None,
    ) -> RunnerResult:
        current_time = now or datetime.now(timezone.utc)
        if current_time.tzinfo is None:
            current_time = current_time.replace(tzinfo=timezone.utc)
        engagement = engagement or build_default_engagement(target, current_time)
        arguments = dict(arguments or {})
        arguments.setdefault("target", target)

        manifest = MANIFESTS.get(adapter_id)
        decision = evaluate_policy(manifest, engagement, target, arguments, now=current_time)
        if not decision.allowed:
            return RunnerResult(status="denied", decision=decision, engagement=engagement, approval=approval)

        approval_decision = validate_approval(approval, engagement, adapter_id, target, now=current_time)
        if not approval_decision.allowed:
            return RunnerResult(
                status="denied",
                decision=approval_decision,
                engagement=engagement,
                approval=approval,
            )

        job = JobEnvelope(
            job_id=f"job-{uuid.uuid4()}",
            tenant_id=engagement.tenant_id,
            client_id=engagement.client_id,
            engagement_id=engagement.engagement_id,
            adapter_id=adapter_id,
            target=decision.normalized_target or target,
            arguments=arguments,
            issued_at=current_time,
            expires_at=current_time + timedelta(seconds=engagement.rules.max_runtime_seconds),
        )
        signed_job = sign_job_envelope(job, self._signing_key)

        runner_decision = validate_job_envelope(
            signed_job,
            manifest,
            engagement,
            self._signing_key,
            now=current_time,
        )
        if not runner_decision.allowed:
            return RunnerResult(
                status="denied",
                decision=runner_decision,
                engagement=engagement,
                approval=approval,
                job=signed_job,
            )

        try:
            evidence = self._simulate_adapter(manifest, signed_job, now=current_time)
        except MockTransportDenied as exc:
            return RunnerResult(
                status="denied",
                decision=PolicyDecision(False, REASON_RATE_LIMIT, f"Mock transport denied: {exc.reason_code}"),
                engagement=engagement,
                approval=approval,
                job=signed_job,
            )

        return RunnerResult(
            status="completed",
            decision=runner_decision,
            engagement=engagement,
            approval=approval,
            job=signed_job,
            evidence=(evidence,),
        )

    def _simulate_adapter(
        self,
        manifest: AdapterManifest,
        job: JobEnvelope,
        now: datetime | None = None,
    ) -> EvidenceRecord:
        if manifest.execution_mode in {
            "fake_transport",
            "mock_transport",
            "governed_transport",
        }:
            payload = self._mock_transport.fetch(manifest.adapter_id, job.target, now=now)
            transport_label = "fake" if manifest.execution_mode == "fake_transport" else "mock"
            content: dict[str, Any] = {
                "adapter_id": manifest.adapter_id,
                "target": job.target,
                "transport": transport_label,
                "observations": payload["observations"],
                "policy_reason": REASON_ALLOW,
            }
            parser_id = f"parser.{manifest.adapter_id}.mock.v1"
            if manifest.adapter_id == "a1.tls.assessment":
                content["observations"] = [
                    {"id": "tls.protocols", "value": ["TLSv1.2", "TLSv1.3"]},
                    {"id": "tls.certificate_chain", "value": "fixture-valid-chain"},
                    {"id": "tls.weak_protocols", "value": []},
                ]
                parser_id = "parser.tls.fixture.v1"
            elif manifest.adapter_id == "a4.tls.cert_expiry":
                content["observations"] = [
                    {"id": "tls.certificate.not_after", "value": "2027-01-01T00:00:00Z"},
                    {"id": "tls.certificate.days_remaining", "value": 365},
                    {"id": "tls.certificate.expired", "value": False},
                    {"id": "tls.certificate.issuer", "value": "Fixture CA"},
                ]
                parser_id = "parser.tls.cert_expiry.fixture.v1"
        elif manifest.adapter_id == "a2.dns.posture":
            content = {
                "adapter_id": manifest.adapter_id,
                "target": job.target,
                "transport": "none",
                "observations": [
                    {"id": "dns.spf", "value": "v=spf1 include:_spf.fixture.example -all"},
                    {"id": "dns.dmarc", "value": "p=reject; rua=mailto:dmarc@fixture.example"},
                    {"id": "dns.dnssec", "value": "enabled-in-fixture"},
                    {"id": "dns.caa", "value": ["0 issue \"letsencrypt.org\""]},
                ],
                "policy_reason": REASON_ALLOW,
            }
            parser_id = "parser.dns.fixture.v1"
        elif manifest.adapter_id == "a3.http.headers":
            content = {
                "adapter_id": manifest.adapter_id,
                "target": job.target,
                "transport": "none",
                "observations": [
                    {"id": "http.strict_transport_security", "value": "max-age=31536000; includeSubDomains"},
                    {"id": "http.content_security_policy", "value": "default-src 'self'"},
                    {"id": "http.x_frame_options", "value": "DENY"},
                    {"id": "http.x_content_type_options", "value": "nosniff"},
                ],
                "policy_reason": REASON_ALLOW,
            }
            parser_id = "parser.http.headers.fixture.v1"
        elif manifest.execution_mode in {"orchestrated_fixture", "export_compiler"}:
            content = {
                "adapter_id": manifest.adapter_id,
                "target": job.target,
                "transport": "orchestrated",
                "observations": [
                    {"id": "orchestration.stage", "value": "fixture-complete"},
                    {"id": "orchestration.mcp_tier", "value": manifest.tier},
                    {"id": "orchestration.execution_mode", "value": manifest.execution_mode},
                ],
                "policy_reason": REASON_ALLOW,
            }
            parser_id = f"parser.{manifest.adapter_id}.orchestrated.v1"
        elif manifest.adapter_id == "mcp.binary.static":
            content = {
                "adapter_id": manifest.adapter_id,
                "target": job.target,
                "transport": "none",
                "observations": [
                    {"id": "binary.arch", "value": "x86_64"},
                    {"id": "binary.pie", "value": True},
                    {"id": "binary.canary", "value": True},
                ],
                "policy_reason": REASON_ALLOW,
            }
            parser_id = "parser.binary.static.fixture.v1"
        else:
            content = {
                "adapter_id": manifest.adapter_id,
                "target": job.target,
                "transport": "none",
                "observations": [
                    {"id": "asset.kind", "value": "fixture-host"},
                    {"id": "service.https", "value": "present-in-fixture"},
                    {"id": "risk.confirmed", "value": False},
                ],
                "policy_reason": REASON_ALLOW,
            }
            parser_id = "parser.inventory.fixture.v1"

        digest = sha256(canonical_json(content).encode("utf-8")).hexdigest()
        return EvidenceRecord(
            evidence_id=f"evidence-{digest[:16]}",
            job_id=job.job_id,
            adapter_id=manifest.adapter_id,
            target=job.target,
            parser_id=parser_id,
            tool_version=manifest.version,
            sha256=digest,
            content=content,
        )