from __future__ import annotations

import json
import os
import secrets
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

Role = Literal["viewer", "operator", "admin"]


@dataclass(frozen=True)
class Principal:
    user_id: str
    role: Role


class KeyStore:
    """Persistent signing key storage for local simulator sessions."""

    def __init__(self, path: str | Path | None = None):
        self.path = Path(path or Path("data") / "signing_key.bin")
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def load_or_create(self) -> bytes:
        if self.path.exists():
            key = self.path.read_bytes()
            if len(key) == 32:
                return key
        key = secrets.token_bytes(32)
        self._write_key(key)
        return key

    def rotate(self) -> bytes:
        key = secrets.token_bytes(32)
        self._write_key(key)
        return key

    def _write_key(self, key: bytes) -> None:
        temp = self.path.with_suffix(".tmp")
        temp.write_bytes(key)
        os.replace(temp, self.path)


class RBAC:
    PERMISSIONS = {
        "viewer": frozenset({"read.audit", "read.evidence", "read.reports"}),
        "operator": frozenset({"read.audit", "read.evidence", "read.reports", "run.simulator", "export.audit"}),
        "admin": frozenset(
            {
                "read.audit",
                "read.evidence",
                "read.reports",
                "run.simulator",
                "export.audit",
                "manage.engagements",
                "rotate.keys",
                "apply.retention",
            }
        ),
    }

    def __init__(self, principal: Principal | None = None):
        self.principal = principal or Principal(user_id="local-operator", role="operator")

    def allowed(self, permission: str) -> bool:
        return permission in self.PERMISSIONS.get(self.principal.role, frozenset())

    def require(self, permission: str) -> None:
        if not self.allowed(permission):
            raise PermissionError(f"Role {self.principal.role} lacks permission {permission}")


def export_audit_filtered(
    events: list[dict[str, Any]],
    *,
    tenant_id: str | None = None,
    engagement_id: str | None = None,
    action: str | None = None,
    reason_code: str | None = None,
) -> str:
    filtered = []
    for event in events:
        if tenant_id and event.get("tenant_id") != tenant_id:
            continue
        if engagement_id and event.get("engagement_id") != engagement_id:
            continue
        if action and event.get("action") != action:
            continue
        if reason_code and event.get("reason_code") != reason_code:
            continue
        filtered.append(event)
    return json.dumps(filtered, indent=2, sort_keys=True, default=str) + "\n"