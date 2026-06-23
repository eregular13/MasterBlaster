"""Multi-consultant utilization dashboard — RBAC-aware engagement and billing visibility."""

from __future__ import annotations

from dataclasses import dataclass

from .client_projects import list_projects
from .p0_storage import P0Storage
from .p4_security import Principal, RBAC
from .p8_auth import LocalAuthStore, LocalUser


@dataclass(frozen=True)
class ConsultantMetric:
    user_id: str
    display_name: str
    role: str
    active_projects: int
    total_usage_units: float
    billable_events: int


def _can_view_financials(rbac: RBAC) -> bool:
    return rbac.principal.role in {"admin", "operator"}


def consultant_metrics(storage: P0Storage, auth_store: LocalAuthStore | None = None) -> tuple[ConsultantMetric, ...]:
    """Aggregate utilization metrics per local user (consultant seat)."""
    store = auth_store or LocalAuthStore()
    users = store.load_users()
    projects = list_projects()
    usage_rows = storage.list_usage_events(limit=5000)

    metrics: list[ConsultantMetric] = []
    for user in users:
        assigned = _projects_for_user(user, projects)
        engagement_ids = {p.engagement_id for p in assigned}
        user_usage = [r for r in usage_rows if r["engagement_id"] in engagement_ids]
        if not assigned and user.role == "admin":
            user_usage = usage_rows
            assigned = projects
        total_units = sum(float(r["quantity"]) for r in user_usage)
        metrics.append(
            ConsultantMetric(
                user_id=user.user_id,
                display_name=user.display_name,
                role=user.role,
                active_projects=len(assigned),
                total_usage_units=total_units,
                billable_events=len(user_usage),
            )
        )
    return tuple(metrics)


def _projects_for_user(user: LocalUser, projects: tuple) -> tuple:
    """Round-robin project assignment by user index for utilization tracking."""
    if user.role == "admin":
        return projects
    users_order = ("viewer", "operator", "admin")
    try:
        user_index = users_order.index(user.role)
    except ValueError:
        user_index = 0
    return tuple(p for i, p in enumerate(projects) if i % len(users_order) == user_index)


def consultant_dashboard_markdown(storage: P0Storage, rbac: RBAC | None = None) -> str:
    auth = LocalAuthStore()
    metrics = consultant_metrics(storage, auth)
    show_financials = rbac is None or _can_view_financials(rbac)
    lines = [
        "# Consultant Utilization Dashboard",
        "",
        "| Consultant | Role | Active Projects | Usage Units | Billable Events |",
        "| --- | --- | ---: | ---: | ---: |",
    ]
    for metric in metrics:
        lines.append(
            f"| {metric.display_name} (`{metric.user_id}`) | {metric.role} | "
            f"{metric.active_projects} | {metric.total_usage_units:g} | {metric.billable_events} |"
        )
    if show_financials:
        total_contract = sum(p.contract_value_usd or 0 for p in list_projects())
        lines.extend([
            "",
            f"**Total contracted value (visible to admin/operator):** ${total_contract:,.0f}",
        ])
    else:
        lines.extend([
            "",
            "_Financial totals restricted to admin/operator roles._",
        ])
    return "\n".join(lines)


def assign_consultant_to_project(project_id: str, consultant_user_id: str) -> bool:
    """Record consultant assignment for utilization tracking."""
    from pathlib import Path
    import json

    path = Path("data") / "business" / "consultant_assignments.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    data = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {"assignments": {}}
    data["assignments"][project_id] = consultant_user_id
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")
    return True