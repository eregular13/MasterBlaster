from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Literal

from .p0_acceptance import acceptance_summary

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
            status="complete",
            blockers=(),
            focus="Ship-ready deny-by-default simulator demo.",
        ),
        PhaseProgress(
            phase_id="P1",
            name="Persistence + CRUD UI",
            percent=100,
            status="complete",
            blockers=(),
            focus="CRUD forms, engagement picker, retention presets, exports.",
        ),
        PhaseProgress(
            phase_id="P2",
            name="Safe live-simulation layer",
            percent=100,
            status="complete",
            blockers=(),
            focus="Mock transport, rate-limit simulator, A5/A6 adapters.",
        ),
        PhaseProgress(
            phase_id="P3",
            name="Advanced orchestration",
            percent=100,
            status="complete",
            blockers=(),
            focus="Findings projection, compliance draft generator, export options.",
        ),
        PhaseProgress(
            phase_id="P4",
            name="Security hardening",
            percent=100,
            status="complete",
            blockers=(),
            focus="Persistent signing keys, RBAC skeleton, filtered audit export.",
        ),
        PhaseProgress(
            phase_id="P5",
            name="Production readiness",
            percent=100,
            status="complete",
            blockers=(),
            focus="Docker, PyInstaller spec, multi-platform CI matrix.",
        ),
        PhaseProgress(
            phase_id="P6",
            name="Community and polish",
            percent=100,
            status="complete",
            blockers=(),
            focus="Contribution guide, issue templates, docs site scaffold.",
        ),
        PhaseProgress(
            phase_id="P7",
            name="Visionary extension",
            percent=100,
            status="complete",
            blockers=(),
            focus="Plugin system design, AI workflow spec, v1.0 release checklist.",
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