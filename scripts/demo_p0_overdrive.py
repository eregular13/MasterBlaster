from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from masterblaster_control.p0_acceptance import acceptance_summary
from masterblaster_control.p0_approvals import approve_request, deny_request, request_approval
from masterblaster_control.p0_resources import list_resources
from masterblaster_control.p0_storage import P0Storage
from masterblaster_control.runner_simulator import MANIFESTS, RunnerSimulator, build_default_engagement


def main() -> int:
    print("=== MasterBlaster P0 Overdrive Demo ===")
    print("Invariant: simulator-only, fixture-only, no network, no child processes, no live tools.")
    print()

    print("Reviewed manifests:")
    for manifest in MANIFESTS.values():
        print(f"- {manifest.adapter_id} | {manifest.tier} | {manifest.execution_mode} | reviewed={manifest.reviewed}")
    print()

    print("Non-executing resources:")
    for resource in list_resources():
        print(f"- {resource.uri} | {resource.category} | non_executing={resource.non_executing}")
    print()

    runner = RunnerSimulator(signing_key=bytes(range(32)))
    storage = P0Storage(":memory:")

    engagement = build_default_engagement("example.com")
    approved = approve_request(request_approval(engagement, "a0.fixture.inventory", "example.com"))
    denied_approval = deny_request(request_approval(engagement, "a0.fixture.inventory", "example.com"))

    completed = runner.run(
        "a0.fixture.inventory",
        "example.com",
        engagement=engagement,
        approval=approved,
    )
    denied = runner.run(
        "a0.fixture.inventory",
        "example.com",
        engagement=engagement,
        approval=denied_approval,
    )

    for result in (completed, denied):
        storage.record_runner_result(result)
        status = result.status.upper()
        print(f"{status}: {result.decision.reason_code} - {result.decision.message}")
        if result.approval:
            print(f"  approval={result.approval.approval_id} state={result.approval.state}")
        if result.job:
            print(f"  job={result.job.job_id} target={result.job.target} signature={result.job.signature[:16]}...")
        for evidence in result.evidence:
            print(f"  evidence={evidence.evidence_id} sha256={evidence.sha256}")
    print()

    snapshot = storage.snapshot()
    print(
        "Storage snapshot: "
        f"tenants={snapshot.tenants}, clients={snapshot.clients}, engagements={snapshot.engagements}, "
        f"approvals={snapshot.approvals}, jobs={snapshot.jobs}, evidence={snapshot.evidence_records}, "
        f"audit={snapshot.audit_events}"
    )

    summary = acceptance_summary()
    print(
        "Acceptance dashboard: "
        f"overall={summary.overall_percent}%, p1_gate={summary.p1_gate_percent}%, "
        f"blockers={len(summary.p1_blockers)}"
    )
    print("Top P1 blockers:")
    for blocker in summary.p1_blockers[:5]:
        print(f"- {blocker}")
    storage.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
