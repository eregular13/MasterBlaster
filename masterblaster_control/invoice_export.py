"""Invoice-oriented export from usage events and project contract values."""

from __future__ import annotations

import json
from datetime import datetime, timezone

from .client_projects import list_projects
from .p0_storage import P0Storage
from .usage_logging import export_usage_csv


def export_invoice_summary_csv(storage: P0Storage) -> str:
    """Produce a finance-friendly CSV combining projects and usage totals."""
    projects = list_projects()
    usage_rows = storage.list_usage_events(limit=5000)
    usage_by_engagement: dict[str, float] = {}
    for row in usage_rows:
        eid = row["engagement_id"]
        usage_by_engagement[eid] = usage_by_engagement.get(eid, 0.0) + float(row["quantity"])

    lines = [
        "project_id,client_name,project_name,engagement_id,contract_value_usd,usage_units,export_date",
    ]
    export_date = datetime.now(timezone.utc).date().isoformat()
    for project in projects:
        usage = usage_by_engagement.get(project.engagement_id, 0.0)
        contract = project.contract_value_usd if project.contract_value_usd is not None else ""
        lines.append(
            f'"{project.project_id}","{project.client_name}","{project.project_name}",'
            f'"{project.engagement_id}","{contract}","{usage:g}","{export_date}"'
        )
    return "\n".join(lines) + "\n"


def export_invoice_summary_json(storage: P0Storage) -> str:
    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "projects": [project.to_dict() for project in list_projects()],
        "usage_csv_available": True,
    }
    return json.dumps(payload, indent=2, sort_keys=True) + "\n"