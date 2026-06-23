import masterblaster_control.client_projects as client_projects
import masterblaster_control.retest_workflow as retest_workflow
from masterblaster_control.accounting_export import export_quickbooks_csv, export_xero_csv
from masterblaster_control.client_portal_dashboard import render_client_portal_html
from masterblaster_control.client_projects import create_project
from masterblaster_control.consultant_dashboard import consultant_dashboard_markdown, consultant_metrics
from masterblaster_control.live_tool_runbook import export_runbook_markdown
from masterblaster_control.p0_storage import P0Storage
from masterblaster_control.professional_reporting import generate_professional_report
from masterblaster_control.retest_workflow import create_retest_campaign, update_retest_item
from masterblaster_control.sow_generator import generate_sow_from_report, sow_markdown
from masterblaster_control.usage_logging import log_usage


def test_client_portal_html(tmp_path, monkeypatch):
    monkeypatch.setattr(client_projects, "PROJECTS_PATH", tmp_path / "projects.json")
    storage = P0Storage(tmp_path / "portal.sqlite3")
    storage.initialize()
    project = create_project(
        storage,
        client_name="Acme Corp",
        project_name="Portal Test",
        template_id="external-pentest",
        scope_targets=("example.com",),
        contract_value_usd=15000.0,
    )
    html = render_client_portal_html(storage, project=project)
    assert "Acme Corp" in html
    assert "Portal Test" in html
    assert "<!DOCTYPE html>" in html


def test_retest_workflow(tmp_path, monkeypatch):
    monkeypatch.setattr(retest_workflow, "RETEST_PATH", tmp_path / "retest.json")
    storage = P0Storage(tmp_path / "retest.sqlite3")
    storage.initialize()
    report = generate_professional_report(
        storage,
        client_name="Client",
        project_name="Retest Project",
    )
    campaign = create_retest_campaign(report)
    assert campaign.campaign_id.startswith("retest-")
    if campaign.items:
        finding_id = campaign.items[0].finding_id
        updated = update_retest_item(campaign.campaign_id, finding_id, status="verified", notes="Fixed")
        assert updated is not None
        assert any(i.status == "verified" for i in updated.items)


def test_accounting_exports(tmp_path, monkeypatch):
    monkeypatch.setattr(client_projects, "PROJECTS_PATH", tmp_path / "projects.json")
    storage = P0Storage(tmp_path / "acct.sqlite3")
    storage.initialize()
    project = create_project(
        storage,
        client_name="Finance Co",
        project_name="Q3 Assessment",
        template_id="web-appsec",
        scope_targets=("app.example.com",),
        contract_value_usd=22000.0,
    )
    log_usage(
        storage,
        tenant_id="tenant-default",
        client_id=project.client_id,
        engagement_id=project.engagement_id,
        event_type="mcp_run",
        quantity=12.0,
    )
    qb = export_quickbooks_csv(storage)
    xero = export_xero_csv(storage)
    assert "Finance Co" in qb
    assert "22000" in qb
    assert "Finance Co" in xero
    assert "SEC-ASSESS" in xero


def test_sow_generator(tmp_path):
    storage = P0Storage(tmp_path / "sow.sqlite3")
    storage.initialize()
    report = generate_professional_report(
        storage,
        client_name="SOW Client",
        project_name="Remediation Sprint",
        template_id="bug-bounty",
    )
    sow, proposal = generate_sow_from_report(report)
    md = sow_markdown(sow, proposal)
    assert "Statement of Work" in md
    assert sow.sow_id.startswith("SOW-")
    assert "Payment terms" in md or "Commercial Terms" in md


def test_consultant_dashboard(tmp_path):
    storage = P0Storage(tmp_path / "consult.sqlite3")
    storage.initialize()
    metrics = consultant_metrics(storage)
    assert len(metrics) >= 3
    md = consultant_dashboard_markdown(storage)
    assert "Consultant Utilization Dashboard" in md


def test_live_tool_runbook():
    text = export_runbook_markdown()
    assert "live_tool_transport" in text
    assert "nmap" in text