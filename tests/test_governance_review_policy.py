import json
from pathlib import Path

from scripts.validate_governance import validate_governance


def test_current_governance_artifacts_validate():
    assert validate_governance() == []


def _minimal_root(tmp_path: Path) -> Path:
    (tmp_path / ".github").mkdir()
    (tmp_path / "docs" / "governance").mkdir(parents=True)
    (tmp_path / "policy").mkdir()
    (tmp_path / ".github" / "pull_request_template.md").write_text(
        "Security impact\nThreat-model impact\nP0 invariant check\nVerification\nDependency changes\n",
        encoding="utf-8",
    )
    (tmp_path / "docs" / "governance" / "security-review-policy.md").write_text(
        "\n".join(
            [
                "## Required Reviewers",
                "## Separation Of Duties",
                "## Prohibited Self-Approval",
                "## Emergency Changes",
                "## Required Evidence",
                "## Threat-Model Update Triggers",
                "## Dependency-Change Review",
                "## Exceptions",
                "## Required Repository Settings",
            ]
        ),
        encoding="utf-8",
    )
    return tmp_path


def test_governance_validator_fails_closed_for_malformed_inventory(tmp_path):
    root = _minimal_root(tmp_path)
    (root / ".github" / "CODEOWNERS").write_text("/masterblaster_control/p0_policy.py @eregular13\n", encoding="utf-8")
    (root / "policy" / "security-sensitive-paths.json").write_text("{not json", encoding="utf-8")

    errors = validate_governance(root)

    assert any("malformed governance inventory" in error for error in errors)


def test_governance_validator_detects_missing_codeowners_coverage(tmp_path):
    root = _minimal_root(tmp_path)
    (root / ".github" / "CODEOWNERS").write_text("", encoding="utf-8")
    (root / "policy" / "security-sensitive-paths.json").write_text(
        json.dumps(
            {
                "review_owner": "@eregular13",
                "security_sensitive_paths": [
                    {
                        "pattern": "/masterblaster_control/p0_policy.py",
                        "category": "policy",
                        "rationale": "scope and policy enforcement",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    errors = validate_governance(root)

    assert "/masterblaster_control/p0_policy.py is missing from CODEOWNERS" in errors


def test_governance_validator_detects_conflicting_codeowners_entries(tmp_path):
    root = _minimal_root(tmp_path)
    (root / ".github" / "CODEOWNERS").write_text(
        "/masterblaster_control/p0_policy.py @eregular13\n"
        "/masterblaster_control/p0_policy.py @someone-else\n",
        encoding="utf-8",
    )
    (root / "policy" / "security-sensitive-paths.json").write_text(
        json.dumps(
            {
                "review_owner": "@eregular13",
                "security_sensitive_paths": [
                    {
                        "pattern": "/masterblaster_control/p0_policy.py",
                        "category": "policy",
                        "rationale": "scope and policy enforcement",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    errors = validate_governance(root)

    assert any("conflicting owners" in error for error in errors)
