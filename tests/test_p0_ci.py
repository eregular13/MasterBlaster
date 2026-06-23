import json
from pathlib import Path

from scripts.generate_sbom_stub import build_sbom


REPO_ROOT = Path(__file__).resolve().parents[1]


def test_sbom_stub_generates_cyclonedx_components(tmp_path):
    output = tmp_path / "sbom.cdx.json"
    payload = build_sbom(REPO_ROOT / "requirements.txt")
    output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    payload = json.loads(output.read_text(encoding="utf-8"))
    assert payload["bomFormat"] == "CycloneDX"
    assert payload["metadata"]["component"]["name"] == "masterblaster-control"
    assert len(payload["components"]) >= 2
    names = {component["name"] for component in payload["components"]}
    assert "PySide6" in names
    assert "pytest" in names


def test_ci_workflow_declares_test_and_sbom_jobs():
    workflow = (REPO_ROOT / ".github" / "workflows" / "p0-ci.yml").read_text(encoding="utf-8")

    assert "python -m pytest" in workflow
    assert "dependency-review-action" in workflow
    assert "generate_sbom_stub.py" in workflow