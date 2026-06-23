from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from .p4_security import Principal, RBAC

Role = Literal["viewer", "operator", "admin"]


@dataclass(frozen=True)
class LocalUser:
    user_id: str
    display_name: str
    role: Role
    auth_provider: str = "local"


class LocalAuthStore:
    """P8 local auth skeleton — no OIDC network calls in v1.0."""

    def __init__(self, path: str | Path | None = None):
        self.path = Path(path or Path("data") / "local_users.json")
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def load_users(self) -> tuple[LocalUser, ...]:
        if not self.path.exists():
            return self._default_users()
        payload = json.loads(self.path.read_text(encoding="utf-8"))
        return tuple(
            LocalUser(
                user_id=item["user_id"],
                display_name=item.get("display_name", item["user_id"]),
                role=item["role"],
                auth_provider=item.get("auth_provider", "local"),
            )
            for item in payload.get("users", [])
        )

    def save_users(self, users: tuple[LocalUser, ...]) -> None:
        payload = {
            "users": [
                {
                    "user_id": user.user_id,
                    "display_name": user.display_name,
                    "role": user.role,
                    "auth_provider": user.auth_provider,
                }
                for user in users
            ]
        }
        self.path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    def authenticate(self, user_id: str) -> RBAC:
        users = {user.user_id: user for user in self.load_users()}
        user = users.get(user_id)
        if not user:
            raise PermissionError(f"Unknown local user: {user_id}")
        return RBAC(Principal(user_id=user.user_id, role=user.role))

    def _default_users(self) -> tuple[LocalUser, ...]:
        users = (
            LocalUser("viewer", "Viewer", "viewer"),
            LocalUser("operator", "Operator", "operator"),
            LocalUser("admin", "Administrator", "admin"),
        )
        self.save_users(users)
        return users