from __future__ import annotations

import secrets
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from hashlib import sha256
import json
from pathlib import Path
from types import MappingProxyType
from typing import Callable, Mapping

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
    REASON_APPROVAL_REPLAY,
    canonical_json,
    evaluate_policy,
    sign_job_envelope,
    validate_job_envelope,
)

_MANIFESTS: dict[str, AdapterManifest] = {
    "a0.fixture.inventory": AdapterManifest(
        adapter_id="a0.fixture.inventory",
        name="A0 Fixture Inventory",
        version="0.1.0",
        tier="A0",
        execution_mode="offline_fixture",
        parameters=("target", "scenario"),
        allowed_target_types=("host", "domain", "ip", "cidr", "url"),
        network_access=False,
        fixture_only=True,
        reviewed=True,
        description="Parses bundled fixture data only. No target network transport is available.",
    ),
    "a1.tls.assessment": AdapterManifest(
        adapter_id="a1.tls.assessment",
        name="A1 TLS Assessment",
        version="0.1.0",
        tier="A1",
        execution_mode="fake_transport",
        parameters=("target", "scenario"),
        allowed_target_types=("domain", "url"),
        network_access=False,
        fixture_only=True,
        reviewed=True,
        description="Exercises the TLS parser behind a fake transport for tests and demos.",
    ),
    "a2.http.headers": AdapterManifest(
        adapter_id="a2.http.headers",
        name="A2 HTTP Header Posture",
        version="0.1.0",
        tier="A2",
        execution_mode="offline_fixture",
        parameters=("target", "scenario"),
        allowed_target_types=("domain", "url"),
        network_access=False,
        fixture_only=True,
        reviewed=True,
        description="Parses checked-in HTTP response-header fixtures only. No HTTP client exists.",
    ),
    "a2.dns.posture": AdapterManifest(
        adapter_id="a2.dns.posture",
        name="A2 DNS Posture",
        version="0.1.0",
        tier="A2",
        execution_mode="offline_fixture",
        parameters=("target", "scenario"),
        allowed_target_types=("domain",),
        network_access=False,
        fixture_only=True,
        reviewed=True,
        description="Parses checked-in DNS posture fixtures only. No resolver exists.",
    ),
    "a2.certificate.expiry": AdapterManifest(
        adapter_id="a2.certificate.expiry",
        name="A2 Certificate Expiry Posture",
        version="0.1.0",
        tier="A2",
        execution_mode="offline_fixture",
        parameters=("target", "scenario"),
        allowed_target_types=("domain", "url"),
        network_access=False,
        fixture_only=True,
        reviewed=True,
        description="Parses checked-in certificate-expiry fixtures only. No socket or TLS transport exists.",
    ),
}

MANIFESTS: Mapping[str, AdapterManifest] = MappingProxyType(_MANIFESTS)
_FIXTURE_ROOT = Path(__file__).resolve().parent / "fixtures"


@dataclass(frozen=True)
class AdapterHandler:
    adapter_id: str
    parser_id: str
    parser_version: str
    fixture_file: str
    default_scenario: str = "healthy"

    @property
    def fixture_path(self) -> Path:
        return _FIXTURE_ROOT / self.fixture_file


_HANDLERS: dict[str, AdapterHandler] = {
    "a0.fixture.inventory": AdapterHandler(
        adapter_id="a0.fixture.inventory",
        parser_id="parser.inventory.fixture",
        parser_version="1.0.0",
        fixture_file="a0_fixture_inventory.json",
    ),
    "a1.tls.assessment": AdapterHandler(
        adapter_id="a1.tls.assessment",
        parser_id="parser.tls.fixture",
        parser_version="1.0.0",
        fixture_file="a1_tls_assessment.json",
    ),
    "a2.http.headers": AdapterHandler(
        adapter_id="a2.http.headers",
        parser_id="parser.http.headers.fixture",
        parser_version="1.0.0",
        fixture_file="a2_http_headers.json",
    ),
    "a2.dns.posture": AdapterHandler(
        adapter_id="a2.dns.posture",
        parser_id="parser.dns.posture.fixture",
        parser_version="1.0.0",
        fixture_file="a2_dns_posture.json",
    ),
    "a2.certificate.expiry": AdapterHandler(
        adapter_id="a2.certificate.expiry",
        parser_id="parser.certificate.expiry.fixture",
        parser_version="1.0.0",
        fixture_file="a2_certificate_expiry.json",
    ),
}
ADAPTER_HANDLERS: Mapping[str, AdapterHandler] = MappingProxyType(_HANDLERS)


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
    def __init__(
        self,
        signing_key: bytes | None = None,
        job_id_factory: Callable[[], str] | None = None,
    ):
        self._signing_key = signing_key or secrets.token_bytes(32)
        self._job_id_factory = job_id_factory or (lambda: f"job-{uuid.uuid4()}")
        self._used_approval_ids: set[str] = set()

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
        if approval and approval.approval_id in self._used_approval_ids:
            return RunnerResult(
                status="denied",
                decision=PolicyDecision(
                    False,
                    REASON_APPROVAL_REPLAY,
                    "Human approval ID has already been consumed by this runner instance.",
                    approval_decision.normalized_target,
                ),
                engagement=engagement,
                approval=approval,
            )

        normalized_target = decision.normalized_target or target
        job = JobEnvelope(
            job_id=self._job_id_factory(),
            tenant_id=engagement.tenant_id,
            client_id=engagement.client_id,
            engagement_id=engagement.engagement_id,
            adapter_id=adapter_id,
            target=normalized_target,
            approval_id=approval.approval_id if approval else "",
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

        evidence = self._simulate_adapter(manifest, signed_job)
        if approval:
            self._used_approval_ids.add(approval.approval_id)
        return RunnerResult(
            status="completed",
            decision=runner_decision,
            engagement=engagement,
            approval=approval,
            job=signed_job,
            evidence=(evidence,),
        )

    def _simulate_adapter(self, manifest: AdapterManifest, job: JobEnvelope) -> EvidenceRecord:
        handler = ADAPTER_HANDLERS.get(manifest.adapter_id)
        if handler is None:
            raise RuntimeError(f"No reviewed handler is registered for {manifest.adapter_id}")
        content, fixture_id = _render_fixture_content(handler, manifest, job)
        draft = EvidenceRecord(
            evidence_id="",
            job_id=job.job_id,
            approval_id=job.approval_id,
            adapter_id=manifest.adapter_id,
            target=job.target,
            parser_id=handler.parser_id,
            parser_version=handler.parser_version,
            fixture_id=fixture_id,
            tool_version=manifest.version,
            sha256="",
            content=content,
        )
        digest = evidence_digest(draft)
        return EvidenceRecord(
            evidence_id=f"evidence-{digest[:16]}",
            job_id=job.job_id,
            approval_id=job.approval_id,
            adapter_id=manifest.adapter_id,
            target=job.target,
            parser_id=handler.parser_id,
            parser_version=handler.parser_version,
            fixture_id=fixture_id,
            tool_version=manifest.version,
            sha256=digest,
            content=content,
        )


def _load_fixture(handler: AdapterHandler) -> dict[str, object]:
    return json.loads(handler.fixture_path.read_text(encoding="utf-8"))


def _render_fixture_content(
    handler: AdapterHandler,
    manifest: AdapterManifest,
    job: JobEnvelope,
) -> tuple[dict[str, object], str]:
    fixture = _load_fixture(handler)
    scenario_id = job.arguments.get("scenario") or handler.default_scenario
    scenarios = fixture.get("scenarios")
    if not isinstance(scenarios, dict):
        scenarios = {}
    scenario = scenarios.get(scenario_id)
    if not isinstance(scenario, dict):
        scenario = {
            "schema_version": "p0.fixture.error.v1",
            "observations": [],
            "notes": f"Unknown scenario '{scenario_id}' rejected by fixture parser.",
        }
    allowed = fixture.get("allowed_observation_ids")
    allowed_ids = set(allowed if isinstance(allowed, list) else [])
    errors: list[str] = []
    if scenario.get("schema_version") != "p0.fixture.v1":
        errors.append("unsupported fixture schema version")
    raw_observations = scenario.get("observations")
    observations: list[object] = raw_observations if isinstance(raw_observations, list) else []
    if not isinstance(raw_observations, list):
        errors.append("observations must be a list")
    for observation in observations:
        if not isinstance(observation, dict) or not isinstance(observation.get("id"), str):
            errors.append("observation entries must contain string IDs")
            continue
        if allowed_ids and observation["id"] not in allowed_ids:
            errors.append(f"unexpected observation id: {observation['id']}")
    parser_status = "accepted" if not errors else "rejected"
    fixture_id = f"{handler.adapter_id}:{scenario_id}:v1"
    return (
        {
            "schema_version": "p0.evidence.v1",
            "adapter_id": manifest.adapter_id,
            "adapter_version": manifest.version,
            "target": job.target,
            "transport": fixture.get("transport", "none"),
            "fixture_id": fixture_id,
            "scenario_id": scenario_id,
            "parser": {
                "id": handler.parser_id,
                "version": handler.parser_version,
                "status": parser_status,
                "errors": sorted(set(errors)),
            },
            "observations": observations,
            "policy_reason": REASON_ALLOW,
        },
        fixture_id,
    )


def evidence_digest_payload(evidence: EvidenceRecord) -> dict[str, object]:
    return {
        "digest_schema": "p0.evidence.digest.v1",
        "evidence_id_scheme": "sha256-first16-v1",
        "job_id": evidence.job_id,
        "approval_id": evidence.approval_id,
        "adapter_id": evidence.adapter_id,
        "adapter_version": evidence.tool_version,
        "target": evidence.target,
        "parser_id": evidence.parser_id,
        "parser_version": evidence.parser_version,
        "fixture_id": evidence.fixture_id,
        "content": evidence.content,
    }


def evidence_digest(evidence: EvidenceRecord) -> str:
    return sha256(canonical_json(evidence_digest_payload(evidence)).encode("utf-8")).hexdigest()


def verify_evidence_record(evidence: EvidenceRecord, job: JobEnvelope | None = None) -> bool:
    digest = evidence_digest(evidence)
    if evidence.sha256 != digest or evidence.evidence_id != f"evidence-{digest[:16]}":
        return False
    if job is None:
        return True
    return (
        evidence.job_id == job.job_id
        and evidence.approval_id == job.approval_id
        and evidence.adapter_id == job.adapter_id
        and evidence.target == job.target
    )


def validate_adapter_handler_registry() -> tuple[str, ...]:
    errors: list[str] = []
    manifest_ids = set(MANIFESTS)
    handler_ids = set(ADAPTER_HANDLERS)
    for adapter_id in sorted(manifest_ids - handler_ids):
        errors.append(f"missing handler for manifest {adapter_id}")
    for adapter_id in sorted(handler_ids - manifest_ids):
        errors.append(f"handler without manifest {adapter_id}")
    for adapter_id, handler in ADAPTER_HANDLERS.items():
        if handler.adapter_id != adapter_id:
            errors.append(f"handler key mismatch for {adapter_id}")
        if not handler.fixture_path.exists():
            errors.append(f"missing fixture file for {adapter_id}: {handler.fixture_file}")
    return tuple(errors)
