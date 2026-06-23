from datetime import datetime, timezone
from pathlib import Path
from masterblaster_control.kali_tool_wrappers import unleash_tool
from masterblaster_control.live_tool_transport import (
    build_live_argv,
    can_execute_live,
    execute_live_tool,
)
from masterblaster_control.p0_models import Engagement, JobEnvelope, RulesOfEngagement, ScopeTarget
from masterblaster_control.p0_policy import REASON_NETWORK_TRANSPORT, evaluate_policy
from masterblaster_control.p0_storage import P0Storage
from masterblaster_control.pdf_report_renderer import render_client_report_pdf
from masterblaster_control.professional_reporting import generate_professional_report
from masterblaster_control.runner_simulator import MANIFESTS, RunnerSimulator, build_default_engagement


def _live_engagement(target: str = "example.com") -> Engagement:
    now = datetime(2026, 6, 23, tzinfo=timezone.utc)
    return Engagement(
        engagement_id="eng-live-test",
        tenant_id="tenant-test",
        client_id="client-test",
        authorized_targets=(ScopeTarget(pattern=target),),
        rules=RulesOfEngagement(allow_network_transport=True, max_runtime_seconds=60),
        expires_at=now.replace(year=2027),
    )


def test_build_live_argv_for_nmap():
    argv = build_live_argv("nmap", "example.com", "syn-top")
    assert argv[0] == "nmap"
    assert "example.com" in argv


def test_can_execute_live_requires_roe():
    engagement = build_default_engagement("example.com")
    assert not can_execute_live(engagement, {"tool": "nmap"})


def test_policy_denies_tool_without_network_roe_when_live_enabled(monkeypatch):
    monkeypatch.setattr(
        "masterblaster_control.p9_feature_flags.is_feature_enabled",
        lambda name, path=None: name == "live_tool_transport",
    )
    manifest = MANIFESTS["a5.port.scan_sim"]
    engagement = build_default_engagement("example.com")
    decision = evaluate_policy(
        manifest, engagement, "example.com", {"target": "example.com", "tool": "nmap"}
    )
    assert not decision.allowed
    assert decision.reason_code == REASON_NETWORK_TRANSPORT


def test_pdf_report_renders(tmp_path):
    storage = P0Storage(tmp_path / "pdf.sqlite3")
    storage.initialize()
    report = generate_professional_report(
        storage,
        client_name="Acme Corp",
        project_name="External Pentest",
        template_id="external-pentest",
    )
    pdf_path = render_client_report_pdf(report, tmp_path / "report.pdf")
    assert pdf_path.exists()
    assert pdf_path.stat().st_size > 2000


def test_live_transport_simulated_fallback_when_binary_missing(tmp_path, monkeypatch):
    monkeypatch.setattr(
        "masterblaster_control.live_tool_transport.is_feature_enabled",
        lambda name, path=None: name == "live_tool_transport",
    )
    engagement = _live_engagement()
    runner = RunnerSimulator(signing_key=bytes(range(32)))
    result = unleash_tool(runner, engagement, "example.com", "nmap", preset_id="syn-top")
    assert result.status == "completed"
    assert result.evidence_id


def test_execute_live_tool_direct(tmp_path, monkeypatch):
    monkeypatch.setattr(
        "masterblaster_control.live_tool_transport.is_feature_enabled",
        lambda name, path=None: name == "live_tool_transport",
    )
    monkeypatch.setattr(
        "masterblaster_control.live_tool_transport.shutil.which",
        lambda _: None,
    )
    engagement = _live_engagement()
    now = datetime(2026, 6, 23, tzinfo=timezone.utc)
    job = JobEnvelope(
        job_id="job-test",
        tenant_id="tenant-test",
        client_id="client-test",
        engagement_id="eng-live-test",
        adapter_id="a5.port.scan_sim",
        target="example.com",
        arguments={"tool": "nmap", "preset": "syn-top", "target": "example.com"},
        issued_at=now,
        expires_at=now.replace(year=2027),
    )
    evidence = execute_live_tool(engagement, job)
    assert evidence.content["transport"] == "simulated-fallback"
    assert any(obs["id"] == "live.mode" for obs in evidence.content["observations"])