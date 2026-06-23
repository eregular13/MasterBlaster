from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Literal

from .p0_acceptance import acceptance_summary
from .p7_plugins import discover_plugins

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
    plugin_count = len(discover_plugins())
    return (
        PhaseProgress("P0", "Simulator perfection", p0.overall_percent, "complete", (), "Ship-ready deny-by-default simulator."),
        PhaseProgress("P1", "Persistence + CRUD UI", 100, "complete", (), "CRUD, engagement picker, retention, exports."),
        PhaseProgress("P2", "Safe live-simulation layer", 100, "complete", (), "Mock transport, rate limit, A5/A6."),
        PhaseProgress("P3", "Advanced orchestration", 100, "complete", (), "Compliance drafts and findings projection."),
        PhaseProgress("P4", "Security hardening", 100, "complete", (), "Signing keys, RBAC, audit export filters."),
        PhaseProgress("P5", "Production readiness", 100, "complete", (), "Docker, PyInstaller, CI matrix."),
        PhaseProgress("P6", "Community and polish", 100, "complete", (), "CONTRIBUTING, templates, docs scaffold."),
        PhaseProgress(
            "P7",
            "Visionary extension",
            100,
            "complete",
            (),
            f"Plugin loader ({plugin_count} plugins), workflow generator, v1.0 assets.",
        ),
        PhaseProgress(
            "P8",
            "Enterprise horizon",
            85,
            "in_progress",
            ("hsm_signing", "codesigned_installer"),
            "v1.0.0 tagged; MCP, auth, hot-reload, pen-test pack, Pages CI shipped.",
        ),
        PhaseProgress(
            "P9",
            "Governed live adapters",
            0,
            "not_started",
            ("a7_review", "live_transport_governance"),
            "A7 live adapter ADR, pen-test pack, star campaign — post-P8.",
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