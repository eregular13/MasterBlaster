import json

from scripts.generate_sbom import build_spdx_document, check_sbom, dependency_inventory, render_spdx_json, write_sbom


def test_dependency_inventory_is_pinned_and_deduplicated():
    inventory = dependency_inventory()
    names = {(item.name.lower(), item.version) for item in inventory}

    assert ("pyside6", "6.7.0") in names
    assert ("pytest", "8.2.2") in names
    assert ("setuptools", "70.0.0") in names
    assert len(names) == len(inventory)


def test_sbom_document_is_deterministic_and_spdx_23():
    first = render_spdx_json(build_spdx_document())
    second = render_spdx_json(build_spdx_document())
    parsed = json.loads(first)

    assert first == second
    assert parsed["spdxVersion"] == "SPDX-2.3"
    assert parsed["creationInfo"]["created"] == "1970-01-01T00:00:00Z"
    assert "C:" not in first
    assert "\\Users\\" not in first


def test_sbom_check_detects_stale_output(tmp_path):
    output = tmp_path / "masterblaster-p0.spdx.json"

    write_sbom(output)
    assert check_sbom(output) == []
    output.write_text("{}", encoding="utf-8")

    assert check_sbom(output)
