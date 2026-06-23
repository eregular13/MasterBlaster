#!/usr/bin/env python3
"""Validate community plugin submissions in marketplace/submissions/."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from masterblaster_control.p7_plugins import PluginLoadError, load_plugin_manifest
from masterblaster_control.p9_plugin_review import discover_submissions, review_queue_markdown

REQUIRED_SUBMISSION_FIELDS = ("submitter", "state")


def validate_submission_dir(path: Path) -> list[str]:
    errors: list[str] = []
    manifest_path = path / "plugin.json"
    if not manifest_path.exists():
        return [f"{path}: missing plugin.json"]

    meta_path = path / "submission.json"
    if not meta_path.exists():
        errors.append(f"{path}: missing submission.json")
        return errors

    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    for field in REQUIRED_SUBMISSION_FIELDS:
        if field not in meta:
            errors.append(f"{path}: submission.json missing {field}")
    state = meta.get("state")
    if state not in {"pending", "approved", "rejected"}:
        errors.append(f"{path}: invalid submission state")

    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    if not payload.get("non_executing", False):
        errors.append(f"{path}: community plugins must be non_executing in v1.0")

    if state == "approved":
        try:
            manifest = load_plugin_manifest(manifest_path)
        except PluginLoadError as exc:
            errors.append(f"{path}: approved submission failed loader: {exc}")
        else:
            if not manifest.reviewed:
                errors.append(f"{path}: approved submission must set reviewed=true")
    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--queue-root", type=Path, default=REPO_ROOT / "marketplace" / "submissions")
    args = parser.parse_args(argv)

    print("=== Validate Plugin Submissions ===")
    errors: list[str] = []
    if not args.queue_root.exists():
        print(review_queue_markdown(args.queue_root))
        print("Queue empty — no submissions to validate.")
        return 0

    for submission_dir in sorted(path for path in args.queue_root.iterdir() if path.is_dir()):
        errors.extend(validate_submission_dir(submission_dir))

    items = discover_submissions(args.queue_root)
    print(review_queue_markdown(args.queue_root))
    print(f"Discovered {len(items)} submission(s).")
    if errors:
        for error in errors:
            print(f"ERROR {error}")
        return 1
    print("All submissions validated.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())