#!/usr/bin/env python3
"""Simulate a full paid engagement: project → pipeline → report → proposal → exports."""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from masterblaster_control.client_projects import create_project
from masterblaster_control.findings_proposal import generate_consulting_proposal, proposal_markdown
from masterblaster_control.invoice_export import export_invoice_summary_csv
from masterblaster_control.pentest_pipeline import execute_assessment_pipeline, pipeline_report_markdown
from masterblaster_control.pdf_report_renderer import default_pdf_output_path, render_client_report_pdf
from masterblaster_control.p0_storage import P0Storage
from masterblaster_control.professional_reporting import (
    export_findings_csv,
    generate_professional_report,
    professional_report_markdown,
)
from masterblaster_control.runner_simulator import RunnerSimulator
from masterblaster_control.utils import write_export_file, write_watermarked_report


def main() -> int:
    target = sys.argv[1] if len(sys.argv) > 1 else "example.com"
    storage = P0Storage.default()
    storage.initialize()
    runner = RunnerSimulator()

    print("=== Paid Engagement Simulation ===")
    project = create_project(
        storage,
        client_name="Acme Corporation",
        project_name="Q2 External Penetration Test",
        template_id="external-pentest",
        scope_targets=(target,),
        contract_value_usd=28000.0,
        allow_live_tools=False,
    )
    print(f"Project: {project.project_name} ({project.engagement_id})")

    engagement = storage.engagement_to_model(storage.get_engagement(project.engagement_id))
    pipeline = execute_assessment_pipeline(
        runner, storage, engagement, target, project.template_id
    )
    print(f"Pipeline: {pipeline.completed} steps completed")
    print(pipeline_report_markdown(pipeline, target)[:800])

    report = generate_professional_report(
        storage,
        engagement_id=project.engagement_id,
        client_name=project.client_name,
        project_name=project.project_name,
        template_id=project.template_id,
    )
    md_path = write_watermarked_report(professional_report_markdown(report), True, prefix="client_report")
    pdf_path = render_client_report_pdf(report, default_pdf_output_path(report))
    proposal = generate_consulting_proposal(report)
    prop_path = write_watermarked_report(proposal_markdown(proposal, report), True, prefix="consulting_proposal")
    csv_path = write_export_file(export_findings_csv(report), "findings_crm", "csv")
    invoice_path = write_export_file(export_invoice_summary_csv(storage), "invoice_summary", "csv")

    print(f"\nDeliverables:")
    print(f"  Markdown report: {md_path}")
    print(f"  PDF report:      {pdf_path}")
    print(f"  Proposal:        {prop_path}")
    print(f"  Findings CSV:    {csv_path}")
    print(f"  Invoice CSV:     {invoice_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())