#!/usr/bin/env python3
"""Generate a professional client assessment report from stored evidence."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from masterblaster_control.findings_proposal import generate_consulting_proposal, proposal_markdown
from masterblaster_control.p0_storage import P0Storage
from masterblaster_control.professional_reporting import (
    export_findings_csv,
    generate_professional_report,
    professional_report_markdown,
)
from masterblaster_control.utils import write_export_file, write_watermarked_report


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate professional client assessment report")
    parser.add_argument("--client", default="Client", help="Client display name")
    parser.add_argument("--project", default="Security Assessment", help="Project name")
    parser.add_argument("--engagement", default="engagement-local-simulator", help="Engagement ID")
    parser.add_argument("--template", default=None, help="Engagement template ID")
    parser.add_argument("--proposal", action="store_true", help="Also generate consulting proposal")
    parser.add_argument("--csv", action="store_true", help="Export findings CSV for CRM")
    args = parser.parse_args()

    storage = P0Storage.default()
    storage.initialize()

    report = generate_professional_report(
        storage,
        engagement_id=args.engagement,
        client_name=args.client,
        project_name=args.project,
        template_id=args.template,
    )
    md = professional_report_markdown(report)
    report_path = write_watermarked_report(md, True, prefix="client_report")
    print(f"Report: {report_path}")
    print(md[:1200] + ("\n..." if len(md) > 1200 else ""))

    if args.proposal:
        proposal = generate_consulting_proposal(report)
        prop_md = proposal_markdown(proposal, report)
        prop_path = write_watermarked_report(prop_md, True, prefix="consulting_proposal")
        print(f"Proposal: {prop_path}")

    if args.csv:
        csv_path = write_export_file(export_findings_csv(report), "findings_crm", "csv")
        print(f"CRM CSV: {csv_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())