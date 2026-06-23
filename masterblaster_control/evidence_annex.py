"""Evidence annex — collects screenshot and artifact references for PDF report appendices."""

from __future__ import annotations

from pathlib import Path

from .p0_storage import P0Storage
from .professional_reporting import ProfessionalReport

EVIDENCE_DIR = Path("data") / "evidence" / "screenshots"
SUPPORTED_EXTENSIONS = {".png", ".jpg", ".jpeg", ".gif", ".webp"}


def discover_evidence_images(
    report: ProfessionalReport,
    storage: P0Storage | None = None,
    *,
    evidence_dir: Path | None = None,
) -> tuple[Path, ...]:
    """Return image paths linked to report evidence IDs or engagement scope."""
    base = evidence_dir or EVIDENCE_DIR
    if not base.exists():
        return ()

    evidence_ids = set(report.evidence_ids)
    images: list[Path] = []
    for path in sorted(base.iterdir()):
        if path.suffix.lower() not in SUPPORTED_EXTENSIONS:
            continue
        name_lower = path.stem.lower()
        if any(eid.lower() in name_lower for eid in evidence_ids):
            images.append(path)
        elif report.engagement_id.lower() in name_lower:
            images.append(path)
    return tuple(images[:12])


def evidence_annex_markdown(report: ProfessionalReport, images: tuple[Path, ...]) -> str:
    lines = [
        "## Evidence Annex",
        "",
        f"**Engagement:** `{report.engagement_id}`",
        f"**Artifacts attached:** {len(images)}",
        "",
    ]
    if not images:
        lines.append("_No screenshot artifacts found. Place images in `data/evidence/screenshots/` named with evidence or engagement IDs._")
        return "\n".join(lines)
    for path in images:
        lines.append(f"- `{path.name}` — linked to assessment evidence")
    return "\n".join(lines)