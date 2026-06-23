from pathlib import Path


def test_p0_verification_workflow_uses_safe_pr_trigger_and_pinned_actions():
    workflow = Path(".github/workflows/p0-verification.yml").read_text(encoding="utf-8")

    assert "pull_request_target" not in workflow
    assert "permissions:\n  contents: read" in workflow
    assert "actions/checkout@34e114876b0b11c390a56381ad16ebd13914f8d5" in workflow
    assert "actions/setup-python@a26af69be951a213d495a4c3e4e4022e16d87065" in workflow
    assert "actions/upload-artifact@ea165f8d65b6e75b540449e92b4886f43607fa02" in workflow
    assert 'python-version: ["3.12"]' in workflow
    assert "sudo apt-get install -y libegl1" in workflow
    assert 'python -m pip install -e ".[dev]"' in workflow
    assert "import masterblaster_control.main_window" in workflow
    assert "QT_QPA_PLATFORM: offscreen" in workflow
    assert "python scripts/scan_prohibited_capabilities.py" in workflow


def test_dependency_review_workflow_has_local_gate_and_fail_closed_github_review():
    workflow = Path(".github/workflows/dependency-review.yml").read_text(encoding="utf-8")

    assert "pull_request_target" not in workflow
    assert "permissions:\n  contents: read\n  pull-requests: read" in workflow
    assert "persist-credentials: false" in workflow
    assert "Deterministic SBOM drift" in workflow
    assert "GitHub dependency review" in workflow
    assert "python scripts/generate_sbom.py --check" in workflow
    assert "actions/dependency-review-action@a1d282b36b6f3519aa1f3fc636f609c47dddb294" in workflow
    assert "timeout-minutes:" in workflow
    assert "continue-on-error" not in workflow
    assert "|| true" not in workflow
