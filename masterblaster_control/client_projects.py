"""Client and project management for professional engagements."""

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path

from .engagement_templates import get_template
from .p0_models import Engagement, RulesOfEngagement, ScopeTarget
from .p0_storage import P0Storage

PROJECTS_PATH = Path("data") / "business" / "projects.json"


@dataclass
class ClientProject:
    project_id: str
    client_id: str
    client_name: str
    project_name: str
    template_id: str
    tenant_id: str
    engagement_id: str
    status: str
    contract_value_usd: float | None
    created_at: str

    def to_dict(self) -> dict:
        return {
            "project_id": self.project_id,
            "client_id": self.client_id,
            "client_name": self.client_name,
            "project_name": self.project_name,
            "template_id": self.template_id,
            "tenant_id": self.tenant_id,
            "engagement_id": self.engagement_id,
            "status": self.status,
            "contract_value_usd": self.contract_value_usd,
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, data: dict) -> ClientProject:
        return cls(
            project_id=str(data["project_id"]),
            client_id=str(data["client_id"]),
            client_name=str(data.get("client_name", data["client_id"])),
            project_name=str(data["project_name"]),
            template_id=str(data["template_id"]),
            tenant_id=str(data.get("tenant_id", "tenant-default")),
            engagement_id=str(data["engagement_id"]),
            status=str(data.get("status", "active")),
            contract_value_usd=data.get("contract_value_usd"),
            created_at=str(data.get("created_at", "")),
        )


def _load_projects() -> list[dict]:
    if not PROJECTS_PATH.exists():
        return []
    return json.loads(PROJECTS_PATH.read_text(encoding="utf-8")).get("projects", [])


def _save_projects(projects: list[dict]) -> None:
    PROJECTS_PATH.parent.mkdir(parents=True, exist_ok=True)
    PROJECTS_PATH.write_text(json.dumps({"projects": projects}, indent=2), encoding="utf-8")


def list_projects() -> tuple[ClientProject, ...]:
    return tuple(ClientProject.from_dict(item) for item in _load_projects())


def create_project(
    storage: P0Storage,
    *,
    client_name: str,
    project_name: str,
    template_id: str,
    scope_targets: tuple[str, ...],
    tenant_id: str = "tenant-default",
    contract_value_usd: float | None = None,
    duration_days: int = 14,
) -> ClientProject:
    template = get_template(template_id)
    if template is None:
        raise ValueError(f"Unknown template: {template_id}")

    client_id = f"client-{uuid.uuid4().hex[:10]}"
    engagement_id = f"eng-{uuid.uuid4().hex[:12]}"
    project_id = f"proj-{uuid.uuid4().hex[:10]}"
    now = datetime.now(timezone.utc)

    storage.create_tenant(tenant_id, tenant_id)
    storage.create_client(client_id, tenant_id, client_name)

    engagement = Engagement(
        engagement_id=engagement_id,
        tenant_id=tenant_id,
        client_id=client_id,
        authorized_targets=tuple(ScopeTarget(pattern=t) for t in scope_targets),
        rules=RulesOfEngagement(
            allow_network_transport=False,
            max_runtime_seconds=120,
            notes=f"Template: {template_id} — {template.name}",
        ),
        expires_at=now + timedelta(days=duration_days),
    )
    storage.save_engagement(engagement)

    project = ClientProject(
        project_id=project_id,
        client_id=client_id,
        client_name=client_name,
        project_name=project_name,
        template_id=template_id,
        tenant_id=tenant_id,
        engagement_id=engagement_id,
        status="active",
        contract_value_usd=contract_value_usd,
        created_at=now.isoformat(),
    )
    projects = _load_projects()
    projects.append(project.to_dict())
    _save_projects(projects)
    return project


def projects_markdown() -> str:
    projects = list_projects()
    lines = [
        "# Client Projects",
        "",
        f"**Active projects:** {len(projects)}",
        "",
        "| Project | Client | Template | Engagement | Status |",
        "| --- | --- | --- | --- | --- |",
    ]
    for project in projects:
        template = get_template(project.template_id)
        template_name = template.name if template else project.template_id
        lines.append(
            f"| {project.project_name} | {project.client_name} | {template_name} | "
            f"`{project.engagement_id}` | {project.status} |"
        )
    if not projects:
        lines.append("| _No projects yet_ | — | — | — | — |")
    return "\n".join(lines)