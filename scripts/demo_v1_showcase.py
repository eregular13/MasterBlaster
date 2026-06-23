from __future__ import annotations

import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from masterblaster_control.p0_acceptance import acceptance_summary
from masterblaster_control.p3_reporting import compliance_draft_markdown, generate_compliance_draft
from masterblaster_control.p7_plugins import discover_plugins, plugin_catalog_markdown
from masterblaster_control.p7_workflow_generator import generate_workflow_draft, workflow_draft_markdown
from masterblaster_control.phase_tracker import phases_dashboard_markdown
from masterblaster_control.p0_storage import P0Storage
from masterblaster_control.runner_simulator import RunnerSimulator, build_default_engagement
from masterblaster_control.p0_approvals import approve_request, request_approval


def main() -> int:
    print("=== MasterBlaster v1.0 Showcase ===")
    summary = acceptance_summary()
    print(f"P0 acceptance: {summary.overall_percent}% | P1 gate: {summary.p1_gate_percent}%")

    storage = P0Storage(":memory:")
    storage.initialize()
    now = datetime(2026, 6, 22, tzinfo=timezone.utc)
    runner = RunnerSimulator(signing_key=bytes(range(32)))
    engagement = build_default_engagement("example.com", now=now)
    approval = approve_request(
        request_approval(engagement, "a5.port.scan_sim", "example.com", now=now),
        now=now,
    )
    result = runner.run("a5.port.scan_sim", "example.com", engagement=engagement, approval=approval, now=now)
    storage.record_runner_result(result)
    print(f"Simulator run: {result.status} evidence={len(result.evidence)}")

    plugins = discover_plugins(REPO_ROOT / "plugins")
    print(plugin_catalog_markdown(plugins))

    workflow = generate_workflow_draft(engagement)
    print(workflow_draft_markdown(workflow))

    compliance = generate_compliance_draft(storage)
    print(compliance_draft_markdown(compliance))

    print(phases_dashboard_markdown())
    print("v1.0 showcase complete — open main.py for the full desktop experience.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())