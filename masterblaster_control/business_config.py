"""Firm branding and billing configuration for client deliverables."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path

CONFIG_PATH = Path("data") / "business" / "firm_config.json"

DEFAULT_FIRM_NAME = "Your Security Firm"
DEFAULT_TAGLINE = "Authorized Security Assessment Services"


@dataclass
class FirmConfig:
    firm_name: str = DEFAULT_FIRM_NAME
    tagline: str = DEFAULT_TAGLINE
    report_watermark: str = "CONFIDENTIAL — Authorized Assessment Report"
    crm_export_prefix: str = "MB"
    default_hourly_rate_usd: float = 225.0
    proposal_valid_days: int = 30
    logo_path: str = ""
    lead_assessor_name: str = "Lead Security Assessor"
    lead_assessor_title: str = "Senior Consultant"
    client_approver_label: str = "Client Authorized Representative"

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> FirmConfig:
        return cls(
            firm_name=str(data.get("firm_name", DEFAULT_FIRM_NAME)),
            tagline=str(data.get("tagline", DEFAULT_TAGLINE)),
            report_watermark=str(data.get("report_watermark", "CONFIDENTIAL — Authorized Assessment Report")),
            crm_export_prefix=str(data.get("crm_export_prefix", "MB")),
            default_hourly_rate_usd=float(data.get("default_hourly_rate_usd", 225.0)),
            proposal_valid_days=int(data.get("proposal_valid_days", 30)),
            logo_path=str(data.get("logo_path", "")),
            lead_assessor_name=str(data.get("lead_assessor_name", "Lead Security Assessor")),
            lead_assessor_title=str(data.get("lead_assessor_title", "Senior Consultant")),
            client_approver_label=str(data.get("client_approver_label", "Client Authorized Representative")),
        )


def load_firm_config() -> FirmConfig:
    if not CONFIG_PATH.exists():
        return FirmConfig()
    return FirmConfig.from_dict(json.loads(CONFIG_PATH.read_text(encoding="utf-8")))


def save_firm_config(config: FirmConfig) -> Path:
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    CONFIG_PATH.write_text(json.dumps(config.to_dict(), indent=2), encoding="utf-8")
    return CONFIG_PATH