"""Client-facing engagement status portal — HTML dashboard for stakeholder visibility."""

from __future__ import annotations

from datetime import datetime, timezone
from html import escape

from .business_config import FirmConfig, load_firm_config
from .client_projects import ClientProject, list_projects
from .engagement_templates import get_template
from .p0_storage import P0Storage
from .professional_reporting import ProfessionalReport, generate_professional_report, SEVERITY_ORDER


def _severity_badge(severity: str) -> str:
    colors = {
        "critical": "#8B0000",
        "high": "#CC3300",
        "medium": "#E67E22",
        "low": "#2980B9",
        "info": "#7F8C8D",
    }
    color = colors.get(severity.lower(), "#555555")
    return f'<span style="background:{color};color:#fff;padding:2px 8px;border-radius:4px;font-size:12px;">{escape(severity.upper())}</span>'


def render_client_portal_html(
    storage: P0Storage,
    *,
    project: ClientProject | None = None,
    report: ProfessionalReport | None = None,
    config: FirmConfig | None = None,
) -> str:
    """Generate a self-contained HTML dashboard suitable for client delivery."""
    cfg = config or load_firm_config()
    projects = [project] if project else list(list_projects())
    if not projects:
        projects = []

    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    rows_html = ""
    for proj in projects:
        template = get_template(proj.template_id)
        template_name = template.name if template else proj.template_id
        contract = f"${proj.contract_value_usd:,.0f}" if proj.contract_value_usd else "—"
        usage_rows = storage.list_usage_events(engagement_id=proj.engagement_id, limit=500)
        usage_total = sum(float(r["quantity"]) for r in usage_rows)
        rows_html += f"""
        <tr>
          <td>{escape(proj.client_name)}</td>
          <td>{escape(proj.project_name)}</td>
          <td>{escape(template_name)}</td>
          <td><code>{escape(proj.engagement_id)}</code></td>
          <td>{escape(proj.status)}</td>
          <td>{contract}</td>
          <td>{usage_total:g}</td>
        </tr>"""

    findings_html = ""
    if report is None and projects:
        proj = projects[0]
        report = generate_professional_report(
            storage,
            engagement_id=proj.engagement_id,
            client_name=proj.client_name,
            project_name=proj.project_name,
            template_id=proj.template_id,
        )
    if report:
        for finding in sorted(
            report.findings,
            key=lambda f: SEVERITY_ORDER.index(f.severity.lower()) if f.severity.lower() in SEVERITY_ORDER else 99,
        ):
            findings_html += f"""
            <tr>
              <td>{_severity_badge(finding.severity)}</td>
              <td>{escape(finding.finding_id)}</td>
              <td>{escape(finding.title)}</td>
              <td>{escape(finding.confidence)}</td>
            </tr>"""
        if not findings_html:
            findings_html = '<tr><td colspan="4" style="text-align:center;color:#666;">No findings recorded</td></tr>'

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1"/>
  <title>{escape(cfg.firm_name)} — Engagement Status</title>
  <style>
    body {{ font-family: 'Segoe UI', system-ui, sans-serif; margin: 0; background: #f4f6f8; color: #1a1a2e; }}
    header {{ background: #1e3a5f; color: #fff; padding: 24px 32px; }}
    header h1 {{ margin: 0 0 4px; font-size: 22px; }}
    header p {{ margin: 0; opacity: 0.85; font-size: 14px; }}
    main {{ max-width: 1100px; margin: 24px auto; padding: 0 16px; }}
    section {{ background: #fff; border-radius: 8px; padding: 20px; margin-bottom: 20px; box-shadow: 0 1px 4px rgba(0,0,0,0.08); }}
    h2 {{ margin: 0 0 16px; font-size: 16px; color: #1e3a5f; }}
    table {{ width: 100%; border-collapse: collapse; font-size: 14px; }}
    th {{ text-align: left; background: #eef2f7; padding: 10px; border-bottom: 2px solid #d0d7e2; }}
    td {{ padding: 10px; border-bottom: 1px solid #e8ecf1; }}
    footer {{ text-align: center; padding: 24px; font-size: 12px; color: #888; }}
    .watermark {{ font-style: italic; color: #666; font-size: 13px; }}
  </style>
</head>
<body>
  <header>
    <h1>{escape(cfg.firm_name)}</h1>
    <p>{escape(cfg.tagline)}</p>
  </header>
  <main>
    <section>
      <h2>Active Engagements</h2>
      <table>
        <thead>
          <tr>
            <th>Client</th><th>Project</th><th>Template</th><th>Engagement</th>
            <th>Status</th><th>Contract</th><th>Usage Units</th>
          </tr>
        </thead>
        <tbody>{rows_html or '<tr><td colspan="7" style="text-align:center;color:#666;">No projects</td></tr>'}</tbody>
      </table>
    </section>
    <section>
      <h2>Findings Overview</h2>
      <table>
        <thead><tr><th>Severity</th><th>ID</th><th>Title</th><th>Confidence</th></tr></thead>
        <tbody>{findings_html or '<tr><td colspan="4" style="text-align:center;color:#666;">Select a project to view findings</td></tr>'}</tbody>
      </table>
    </section>
    <p class="watermark">{escape(cfg.report_watermark)}</p>
  </main>
  <footer>Generated {now} — {escape(cfg.firm_name)}</footer>
</body>
</html>"""