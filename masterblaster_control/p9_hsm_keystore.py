from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from .p4_security import KeyStore
from .p9_feature_flags import is_feature_enabled


class SigningKeyProvider(Protocol):
    def load_signing_key(self) -> bytes: ...


@dataclass(frozen=True)
class HSMKeyReference:
    provider: str
    key_id: str
    path: str | None = None

    def to_dict(self) -> dict[str, object]:
        return {"provider": self.provider, "key_id": self.key_id, "path": self.path}


class ExternalHSMKeyStore:
    """P9 HSM skeleton — resolves key material from env/file pointer, not live PKCS#11."""

    def __init__(self, reference: HSMKeyReference | None = None, fallback: KeyStore | None = None):
        self.reference = reference or HSMKeyReference(
            provider=os.environ.get("MB_HSM_PROVIDER", "local-file"),
            key_id=os.environ.get("MB_HSM_KEY_ID", "simulator-default"),
            path=os.environ.get("MB_HSM_KEY_PATH"),
        )
        self.fallback = fallback or KeyStore()

    def load_signing_key(self) -> bytes:
        if not is_feature_enabled("hsm_signing"):
            return self.fallback.load_or_create()
        if self.reference.path:
            key_path = Path(self.reference.path)
            if key_path.exists():
                key = key_path.read_bytes()
                if len(key) == 32:
                    return key
        return self.fallback.load_or_create()

    def status_markdown(self) -> str:
        enabled = is_feature_enabled("hsm_signing")
        return (
            f"# HSM Key Store Status\n\n"
            f"- Feature enabled: **{'yes' if enabled else 'no'}**\n"
            f"- Provider: `{self.reference.provider}`\n"
            f"- Key ID: `{self.reference.key_id}`\n"
            f"- Path: `{self.reference.path or '(fallback local KeyStore)'}`\n"
        )