"""Consultant runbook for governed live tool transport — exportable operational guide."""

from __future__ import annotations

RUNBOOK_TEXT = """# Live Tool Transport — Consultant Runbook

## Overview
Live tool transport executes registered security tools (nmap, nuclei, sqlmap, ffuf, subfinder)
via a governed subprocess boundary. All execution requires explicit authorization.

## Prerequisites
1. Security tools installed and available on system PATH
2. Signed rules of engagement with in-scope targets
3. Feature flag enabled: `data/feature_flags.json` → `"live_tool_transport": true`
4. Project ROE: "Authorize live tool transport" checked at project creation

## Authorization Gates (all required)
| Gate | Setting |
| --- | --- |
| Feature flag | `live_tool_transport` = true |
| ROE | `allow_network_transport` = true |
| Tool registry | Tool ID in `KALI_TOOL_REGISTRY` |
| Scope | Target matches engagement authorized targets |
| Policy | Human approval envelope signed |

## Enabling Live Transport
```json
// data/feature_flags.json
{
  "flags": {
    "live_tool_transport": true
  }
}
```

## Execution Paths
- **GUI:** Tool Integrations tab → select tool → UNLEASH (with active authorized engagement)
- **CLI:** `python scripts/unleash_arsenal.py --tool nmap --target example.com`
- **Pipeline:** Assessment pipeline routes tool strikes through live transport when gates pass

## Fallback Behavior
If the tool binary is not found on PATH, the system records a `simulated-fallback` result
with audit metadata. This preserves workflow continuity during dry-runs.

## Audit & Billing
- Every live execution produces evidence records and usage events
- Export usage via Clients & Projects → Export Usage CSV (Billing)
- Invoice summary combines contract value + usage units

## Safety Checklist
- [ ] ROE signed and scope verified
- [ ] Feature flag enabled only for authorized engagement window
- [ ] Client notification sent per contract terms
- [ ] Live transport disabled after engagement completion

## Support
Review `ethics.md` and engagement notes in Records tab for policy details.
"""


def export_runbook_markdown() -> str:
    return RUNBOOK_TEXT


def export_runbook_plain() -> str:
    return RUNBOOK_TEXT.replace("```json", "").replace("```", "")