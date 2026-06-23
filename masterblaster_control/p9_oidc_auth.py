from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Literal
from urllib.parse import urlencode

from .p4_security import Principal, RBAC
from .p9_feature_flags import is_feature_enabled

Role = Literal["viewer", "operator", "admin"]


@dataclass(frozen=True)
class OIDCProviderConfig:
    issuer: str
    client_id: str
    redirect_uri: str
    default_role: Role = "viewer"
    scopes: tuple[str, ...] = ("openid", "profile", "email")

    def to_dict(self) -> dict[str, object]:
        return {
            "issuer": self.issuer,
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "default_role": self.default_role,
            "scopes": list(self.scopes),
        }

    def authorization_url(self, state: str = "mb-local-state") -> str:
        query = urlencode(
            {
                "client_id": self.client_id,
                "redirect_uri": self.redirect_uri,
                "response_type": "code",
                "scope": " ".join(self.scopes),
                "state": state,
            }
        )
        return f"{self.issuer.rstrip('/')}/authorize?{query}"


class OIDCAuthStore:
    """P9 OIDC skeleton — builds URLs and maps claims; no token exchange network calls."""

    def __init__(self, path: str | Path | None = None):
        self.path = Path(path or Path("data") / "oidc_config.json")
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def load_config(self) -> OIDCProviderConfig:
        if not self.path.exists():
            config = OIDCProviderConfig(
                issuer="https://login.example.com/realms/masterblaster",
                client_id="masterblaster-desktop",
                redirect_uri="http://127.0.0.1:8765/callback",
            )
            self.save_config(config)
            return config
        payload = json.loads(self.path.read_text(encoding="utf-8"))
        return OIDCProviderConfig(
            issuer=str(payload["issuer"]),
            client_id=str(payload["client_id"]),
            redirect_uri=str(payload["redirect_uri"]),
            default_role=payload.get("default_role", "viewer"),
            scopes=tuple(str(item) for item in payload.get("scopes", ["openid", "profile", "email"])),
        )

    def save_config(self, config: OIDCProviderConfig) -> None:
        self.path.write_text(json.dumps(config.to_dict(), indent=2, sort_keys=True) + "\n", encoding="utf-8")

    def authenticate_claims(self, claims: dict[str, object]) -> RBAC:
        if not is_feature_enabled("oidc_auth"):
            raise PermissionError("OIDC auth feature flag is disabled.")
        sub = str(claims.get("sub", "oidc-user"))
        role = claims.get("mb_role", self.load_config().default_role)
        if role not in {"viewer", "operator", "admin"}:
            role = self.load_config().default_role
        return RBAC(Principal(user_id=sub, role=role))  # type: ignore[arg-type]

    def scaffold_markdown(self) -> str:
        config = self.load_config()
        enabled = is_feature_enabled("oidc_auth")
        return (
            "# OIDC Auth Scaffold\n\n"
            f"- Feature enabled: **{'yes' if enabled else 'no'}**\n"
            f"- Issuer: `{config.issuer}`\n"
            f"- Client ID: `{config.client_id}`\n"
            f"- Redirect: `{config.redirect_uri}`\n"
            f"- Authorization URL (offline): `{config.authorization_url()}`\n"
        )