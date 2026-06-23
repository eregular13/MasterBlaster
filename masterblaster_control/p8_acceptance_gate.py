from __future__ import annotations

from dataclasses import dataclass

from .phase_tracker import list_phase_progress


@dataclass(frozen=True)
class P8AcceptanceGate:
    percent: int
    passed: bool
    blockers: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return {"percent": self.percent, "passed": self.passed, "blockers": list(self.blockers)}


def evaluate_p8_gate() -> P8AcceptanceGate:
    phase = next(item for item in list_phase_progress() if item.phase_id == "P8")
    blockers = phase.blockers
    passed = phase.percent >= 100 and not blockers
    return P8AcceptanceGate(percent=phase.percent, passed=passed, blockers=blockers)


def p8_gate_markdown() -> str:
    gate = evaluate_p8_gate()
    blockers = ", ".join(gate.blockers) if gate.blockers else "none"
    status = "PASSED" if gate.passed else "IN PROGRESS"
    return (
        f"# P8 Acceptance Gate\n\n"
        f"- Status: **{status}**\n"
        f"- Progress: **{gate.percent}%**\n"
        f"- Blockers: {blockers}\n"
    )