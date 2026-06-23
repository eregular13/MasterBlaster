from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
INVENTORY_PATH = Path("policy/security-sensitive-paths.json")
CODEOWNERS_PATH = Path(".github/CODEOWNERS")
POLICY_DOC_PATH = Path("docs/governance/security-review-policy.md")
PR_TEMPLATE_PATH = Path(".github/pull_request_template.md")

REQUIRED_POLICY_SECTIONS = (
    "Required Reviewers",
    "Separation Of Duties",
    "Prohibited Self-Approval",
    "Emergency Changes",
    "Required Evidence",
    "Threat-Model Update Triggers",
    "Dependency-Change Review",
    "Exceptions",
    "Required Repository Settings",
)

REQUIRED_PR_FIELDS = (
    "Security impact",
    "Threat-model impact",
    "P0 invariant check",
    "Verification",
    "Dependency changes",
)


@dataclass(frozen=True)
class CodeownersEntry:
    pattern: str
    owners: tuple[str, ...]
    line_number: int


def _load_inventory(root: Path) -> dict[str, Any]:
    path = root / INVENTORY_PATH
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ValueError(f"missing governance inventory: {INVENTORY_PATH}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"malformed governance inventory: {exc}") from exc
    if not isinstance(data, dict):
        raise ValueError("governance inventory must be a JSON object")
    return data


def _parse_codeowners(root: Path) -> list[CodeownersEntry]:
    path = root / CODEOWNERS_PATH
    if not path.exists():
        raise ValueError(f"missing CODEOWNERS file: {CODEOWNERS_PATH}")
    entries: list[CodeownersEntry] = []
    for line_number, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        stripped = raw.strip()
        if not stripped or stripped.startswith("#"):
            continue
        parts = stripped.split()
        if len(parts) < 2:
            raise ValueError(f"CODEOWNERS line {line_number} has no owner")
        entries.append(CodeownersEntry(parts[0], tuple(parts[1:]), line_number))
    return entries


def validate_governance(root: Path = REPO_ROOT) -> list[str]:
    errors: list[str] = []
    try:
        inventory = _load_inventory(root)
    except ValueError as exc:
        return [str(exc)]
    try:
        entries = _parse_codeowners(root)
    except ValueError as exc:
        return [str(exc)]

    owner = inventory.get("review_owner")
    if owner != "@eregular13":
        errors.append("review_owner must be the repository owner @eregular13")

    paths = inventory.get("security_sensitive_paths")
    if not isinstance(paths, list) or not paths:
        errors.append("security_sensitive_paths must be a non-empty list")
        paths = []

    pattern_to_entries: dict[str, list[CodeownersEntry]] = {}
    for entry in entries:
        pattern_to_entries.setdefault(entry.pattern, []).append(entry)
    for pattern, duplicates in sorted(pattern_to_entries.items()):
        owner_sets = {duplicate.owners for duplicate in duplicates}
        if len(owner_sets) > 1:
            errors.append(f"CODEOWNERS pattern {pattern} has conflicting owners")

    inventory_patterns: set[str] = set()
    for index, item in enumerate(paths):
        if not isinstance(item, dict):
            errors.append(f"security_sensitive_paths[{index}] must be an object")
            continue
        pattern = item.get("pattern")
        category = item.get("category")
        rationale = item.get("rationale")
        if not isinstance(pattern, str) or not pattern.startswith("/"):
            errors.append(f"security_sensitive_paths[{index}] has invalid pattern")
            continue
        if pattern in inventory_patterns:
            errors.append(f"duplicate sensitive path pattern: {pattern}")
        inventory_patterns.add(pattern)
        if not isinstance(category, str) or not category:
            errors.append(f"{pattern} is missing category")
        if not isinstance(rationale, str) or len(rationale) < 12:
            errors.append(f"{pattern} is missing a useful rationale")
        entries_for_pattern = pattern_to_entries.get(pattern, [])
        if not entries_for_pattern:
            errors.append(f"{pattern} is missing from CODEOWNERS")
        elif owner not in entries_for_pattern[-1].owners:
            errors.append(f"{pattern} CODEOWNERS entry does not include {owner}")

    for entry in entries:
        if entry.pattern.startswith("/") and entry.pattern not in inventory_patterns:
            errors.append(f"CODEOWNERS pattern {entry.pattern} is not in the sensitive-path inventory")

    policy_text = (root / POLICY_DOC_PATH).read_text(encoding="utf-8") if (root / POLICY_DOC_PATH).exists() else ""
    if not policy_text:
        errors.append(f"missing security review policy doc: {POLICY_DOC_PATH}")
    for section in REQUIRED_POLICY_SECTIONS:
        if f"## {section}" not in policy_text:
            errors.append(f"security review policy missing section: {section}")

    pr_template = (root / PR_TEMPLATE_PATH).read_text(encoding="utf-8") if (root / PR_TEMPLATE_PATH).exists() else ""
    if not pr_template:
        errors.append(f"missing pull request template: {PR_TEMPLATE_PATH}")
    for field in REQUIRED_PR_FIELDS:
        if field not in pr_template:
            errors.append(f"pull request template missing field: {field}")

    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate MasterBlaster security review governance artifacts.")
    parser.parse_args(argv)
    errors = validate_governance(REPO_ROOT)
    for error in errors:
        print(f"ERROR: {error}", file=sys.stderr)
    if errors:
        return 1
    print("Governance review policy validated.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
