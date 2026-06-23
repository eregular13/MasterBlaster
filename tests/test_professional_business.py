from datetime import datetime, timezone

import masterblaster_control.client_projects as client_projects
from masterblaster_control.client_projects import create_project, list_projects
from masterblaster_control.engagement_templates import ENGAGEMENT_TEMPLATES, get_template
from masterblaster_control.findings_proposal import generate_consulting_proposal, proposal_markdown
from masterblaster_control.pentest_pipeline import execute_assessment_pipeline
from masterblaster_control.p0_storage import P0Storage
from masterblaster_control.professional_reporting import (
    generate_professional_report,
    professional_report_markdown,
)
from masterblaster_control.runner_simulator import RunnerSimulator, build_default_engagement
from masterblaster_control.usage_logging import log_usage, usage_summary_markdown


def test_engagement_templates_cover_core_offerings():
    assert "external-pentest" in ENGAGEMENT_TEMPLATES
    assert "web-appsec" in ENGAGEMENT_TEMPLATES
    assert "bug-bounty" in ENGAGEMENT_TEMPLATES


def test_create_project_and_pipeline(tmp_path, monkeypatch):
    monkeypatch.setattr(client_projects, "PROJECTS_PATH", tmp_path / "projects.json")
    storage = P0Storage(tmp_path / "biz.sqlite3")
    storage.initialize()
    project = create_project(
        storage,
        client_name="Acme Corp",
        project_name="External Pentest Q2",
        template_id="external-pentest",
        scope_targets=("example.com",),
        contract_value_usd=25000.0,
    )
    assert project.engagement_id
    assert len(list_projects()) >= 1

    now = datetime(2026, 6, 23, tzinfo=timezone.utc)
    runner = RunnerSimulator(signing_key=bytes(range(32)))
    engagement = build_default_engagement("example.com", now=now)
    engagement = storage.engagement_to_model(storage.get_engagement(project.engagement_id))
    result = execute_assessment_pipeline(
        runner, storage, engagement, "example.com", "external-pentest", now=now
    )
    assert result.completed >= 3


def test_professional_report_and_proposal(tmp_path):
    storage = P0Storage(tmp_path / "report.sqlite3")
    storage.initialize()
    log_usage(
        storage,
        tenant_id="tenant-default",
        client_id="client-test",
        engagement_id="engagement-local-simulator",
        event_type="report_generation",
        quantity=1.0,
    )
    report = generate_professional_report(
        storage,
        client_name="Acme Corp",
        project_name="Web App Assessment",
        template_id="web-appsec",
    )
    md = professional_report_markdown(report)
    assert "Executive Summary" in md
    assert "Compliance Appendix" in md
    proposal = generate_consulting_proposal(report)
    prop_md = proposal_markdown(proposal, report)
    assert "Consulting Services Proposal" in prop_md
    assert proposal.total_value_usd >= 0


def test_usage_summary(tmp_path):
    storage = P0Storage(tmp_path / "usage.sqlite3")
    storage.initialize()
    log_usage(
        storage,
        tenant_id="t1",
        client_id="c1",
        engagement_id="e1",
        event_type="mcp_execution",
        quantity=5,
    )
    md = usage_summary_markdown(storage)
    assert "mcp_execution" in md