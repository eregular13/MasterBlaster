#!/usr/bin/env python3
"""Generate GitHub release notes from CHANGELOG.md and marketing assets."""

from __future__ import annotations

import argparse
import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
CHANGELOG = REPO_ROOT / "CHANGELOG.md"
ANNOUNCEMENT = REPO_ROOT / "docs" / "marketing" / "ANNOUNCEMENT.md"
OUTPUT_DEFAULT = REPO_ROOT / "dist" / "RELEASE_NOTES.md"


def extract_version_section(changelog_text: str, version: str) -> str:
    pattern = rf"## \[{re.escape(version)}\][^\n]*\n(.*?)(?=\n## \[|\Z)"
    match = re.search(pattern, changelog_text, flags=re.DOTALL)
    if not match:
        raise ValueError(f"Version {version} not found in CHANGELOG.md")
    return match.group(1).strip()


def generate_release_notes(version: str, *, include_announcement: bool = True) -> str:
    changelog = CHANGELOG.read_text(encoding="utf-8")
    section = extract_version_section(changelog, version)
    lines = [
        f"# MasterBlaster {version}",
        "",
        "> Deny-by-default authorized assessment control plane — simulator only.",
        "",
        "## Changelog",
        "",
        section,
        "",
    ]
    if include_announcement and ANNOUNCEMENT.exists():
        lines.extend(
            [
                "## Community Announcement",
                "",
                ANNOUNCEMENT.read_text(encoding="utf-8").strip(),
                "",
            ]
        )
    lines.extend(
        [
            "## Quick Start",
            "",
            "```bash",
            "git clone https://github.com/eregular13/MasterBlaster.git",
            "git checkout grok/masterblaster",
            "pip install -r requirements.txt",
            "python -m pytest",
            "python scripts/demo_v1_showcase.py",
            "python main.py",
            "```",
            "",
            "## Ethics",
            "",
            "Authorized assessments only. Simulator output is evidence drafts — not certification.",
        ]
    )
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--version", default="1.0.0")
    parser.add_argument("--output", type=Path, default=OUTPUT_DEFAULT)
    parser.add_argument("--no-announcement", action="store_true")
    args = parser.parse_args(argv)

    notes = generate_release_notes(args.version, include_announcement=not args.no_announcement)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(notes, encoding="utf-8")
    print(f"Wrote {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())