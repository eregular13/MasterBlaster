from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Literal

from .p0_acceptance import acceptance_summary, list_acceptance_criteria

PhaseStatusLabel = Literal["complete", "in_progress", "not_started"]


@dataclass(frozen=True)
class PhaseProgress:
    phase_id: str
    name: str
    percent: int
    status: PhaseStatusLabel
    blockers: tuple[str, ...]
    focus: str

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def list_phase_progress() -> tuple[PhaseProgress, ...]:
    p0 = acceptance_summary()
    return (
        PhaseProgress(
            phase_id="P0",
            name="Simulator perfection",
            percent=p0.overall_percent,
            status="complete" if p0.overall_percent >= 100 else "in_progress",
            blockers=() if p0.overall_percent >= 100 else tuple(
                criterion.criterion_id
                for criterion in list_acceptance_criteria()
                if criterion.percent < 100
            ),
            focus="100% acceptance dashboard, deny-by-default simulator, ship-ready demo.",
        ),
        PhaseProgress(
            phase_id="P1",
            name="Persistence + CRUD UI",
            percent=55,
            status="in_progress",
            blockers=("engagement.edit_delete", "retention_presets_ui", "engagement_picker_ui"),
            focus="Edit/delete flows, retention presets, engagement picker in simulator tabs.",
        ),
        PhaseProgress(
            phase_id="P2",
            name="Safe live-simulation layer",
            percent=0,
            status="not_started",
            blockers=("p0.acceptance_complete", "mock_transport_design"),
            focus="Mock transport, rate-limit sim, A3+ adapters without real network.",
        ),
        PhaseProgress(
            phase_id="P3",
            name="Advanced orchestration",
            percent=0,
            status="not_started",
            blockers=("p2.complete",),
            focus="MCP planning engine, reporting engine, compliance draft generator.",
        ),
        PhaseProgress(
            phase_id="P4",
            name="Security hardening",
            percent=0,
            status="not_started",
            blockers=("p3.complete",),
            focus="Real signing keys, RBAC, audit export, SBOM enforcement.",
        ),
        PhaseProgress(
            phase_id="P5",
            name="Production readiness",
            percent=0,
            status="not_started",
            blockers=("p4.complete",),
            focus="Docker, multi-platform builds, installer, telemetry opt-in.",
        ),
        PhaseProgress(
            phase_id="P6",
            name="Community and polish",
            percent=0,
            status="not_started",
            blockers=("p5.complete",),
            focus="Docs site, contribution guide, GitHub templates, demo assets.",
        ),
        PhaseProgress(
            phase_id="P7",
            name="Visionary extension",
            percent=0,
            status="not_started",
            blockers=("p6.complete",),
            focus="AI workflow generator, plugin system, v1.0 release prep.",
        ),
    )


def phases_dashboard_markdown() -> str:
    lines = [
        "# MasterBlaster Phase Roadmap",
        "",
        "| Phase | Name | % | Status | Blockers | Focus |",
        "| --- | --- | ---: | --- | --- | --- |",
    ]
    for phase in list_phase_progress():
        blockers = ", ".join(phase.blockers) if phase.blockers else "—"
        lines.append(
            f"| {phase.phase_id} | {phase.name} | {phase.percent}% | "
            f"{phase.status} | {blockers} | {phase.focus} |"
        )
    return "\n".join(lines)