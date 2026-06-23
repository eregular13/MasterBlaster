"""Accounting system exports — QuickBooks Online and Xero compatible invoice CSV."""

from __future__ import annotations

from datetime import datetime, timezone

from .business_config import load_firm_config
from .client_projects import list_projects
from .p0_storage import P0Storage


def export_quickbooks_csv(storage: P0Storage) -> str:
    """QuickBooks Online import format — one row per project invoice line."""
    cfg = load_firm_config()
    projects = list_projects()
    usage_rows = storage.list_usage_events(limit=5000)
    usage_by_engagement: dict[str, float] = {}
    for row in usage_rows:
        eid = row["engagement_id"]
        usage_by_engagement[eid] = usage_by_engagement.get(eid, 0.0) + float(row["quantity"])

    invoice_date = datetime.now(timezone.utc).date().isoformat()
    lines = [
        "InvoiceNo,Customer,InvoiceDate,DueDate,Item(Product/Service),ItemDescription,"
        "ItemQuantity,ItemRate,ItemAmount,Currency",
    ]
    for project in projects:
        if project.contract_value_usd is None:
            continue
        invoice_no = f"{cfg.crm_export_prefix}-{project.project_id[-8:].upper()}"
        usage = usage_by_engagement.get(project.engagement_id, 0.0)
        description = (
            f"{project.project_name} — security assessment engagement "
            f"({project.engagement_id}); usage units: {usage:g}"
        )
        lines.append(
            f'"{invoice_no}","{project.client_name}","{invoice_date}","{invoice_date}",'
            f'"Security Assessment","{description}",1,{project.contract_value_usd:g},'
            f'{project.contract_value_usd:g},USD'
        )
    return "\n".join(lines) + "\n"


def export_xero_csv(storage: P0Storage) -> str:
    """Xero invoice import format."""
    cfg = load_firm_config()
    projects = list_projects()
    usage_rows = storage.list_usage_events(limit=5000)
    usage_by_engagement: dict[str, float] = {}
    for row in usage_rows:
        eid = row["engagement_id"]
        usage_by_engagement[eid] = usage_by_engagement.get(eid, 0.0) + float(row["quantity"])

    invoice_date = datetime.now(timezone.utc).date().isoformat()
    lines = [
        "*ContactName,EmailAddress,POAddressLine1,*InvoiceNumber,*InvoiceDate,*DueDate,"
        "InventoryItemCode,*Description,*Quantity,*UnitAmount,*AccountCode,*TaxType,Currency",
    ]
    for project in projects:
        if project.contract_value_usd is None:
            continue
        invoice_no = f"{cfg.crm_export_prefix}-{project.project_id[-8:].upper()}"
        usage = usage_by_engagement.get(project.engagement_id, 0.0)
        description = (
            f"{project.project_name} — authorized security assessment "
            f"(engagement {project.engagement_id}; {usage:g} usage units)"
        )
        lines.append(
            f'"{project.client_name}",,"","{invoice_no}","{invoice_date}","{invoice_date}",'
            f'"SEC-ASSESS","{description}",1,{project.contract_value_usd:g},'
            f'"4000","Tax Exempt",USD'
        )
    return "\n".join(lines) + "\n"