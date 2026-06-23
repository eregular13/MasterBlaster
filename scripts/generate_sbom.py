from __future__ import annotations

import argparse
import json
import re
import sys
import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = REPO_ROOT / "sbom" / "masterblaster-p0.spdx.json"
FIXED_CREATED = "1970-01-01T00:00:00Z"
SPDX_VERSION = "SPDX-2.3"
TOOL_NAME = "MasterBlaster-P0-SBOM-Generator"
TOOL_VERSION = "1.0"


@dataclass(frozen=True, order=True)
class DependencySpec:
    name: str
    version: str
    source: str
    scope: str

    @property
    def package_spdx_id(self) -> str:
        safe = re.sub(r"[^A-Za-z0-9.-]+", "-", self.name.lower()).strip("-")
        return f"SPDXRef-Package-{safe}"


def _load_pyproject(root: Path) -> dict:
    with (root / "pyproject.toml").open("rb") as pyproject_file:
        return tomllib.load(pyproject_file)


def _parse_pinned_requirement(raw: str, source: str, scope: str) -> DependencySpec:
    value = raw.strip()
    if not value or value.startswith("#"):
        raise ValueError("empty requirement lines are not dependency specs")
    if "==" not in value:
        raise ValueError(f"{source} contains an unpinned dependency: {value}")
    name, version = value.split("==", 1)
    name = name.strip()
    version = version.strip()
    if not name or not version or any(ch.isspace() for ch in name + version):
        raise ValueError(f"{source} contains malformed dependency pin: {value}")
    return DependencySpec(name=name, version=version, source=source, scope=scope)


def dependency_inventory(root: Path = REPO_ROOT) -> tuple[DependencySpec, ...]:
    pyproject = _load_pyproject(root)
    specs: list[DependencySpec] = []
    for requirement in pyproject.get("build-system", {}).get("requires", []):
        specs.append(_parse_pinned_requirement(requirement, "pyproject.toml:build-system.requires", "build"))
    for requirement in pyproject.get("project", {}).get("dependencies", []):
        specs.append(_parse_pinned_requirement(requirement, "pyproject.toml:project.dependencies", "runtime"))
    for extra_name, requirements in sorted(pyproject.get("project", {}).get("optional-dependencies", {}).items()):
        for requirement in requirements:
            specs.append(_parse_pinned_requirement(requirement, f"pyproject.toml:project.optional-dependencies.{extra_name}", f"optional:{extra_name}"))

    requirements_path = root / "requirements.txt"
    if requirements_path.exists():
        for line_number, line in enumerate(requirements_path.read_text(encoding="utf-8").splitlines(), start=1):
            stripped = line.strip()
            if stripped and not stripped.startswith("#"):
                specs.append(_parse_pinned_requirement(stripped, f"requirements.txt:{line_number}", "requirements"))

    deduped: dict[tuple[str, str], DependencySpec] = {}
    for spec in specs:
        key = (spec.name.lower(), spec.version)
        existing = deduped.get(key)
        if existing is None:
            deduped[key] = spec
        else:
            deduped[key] = DependencySpec(
                name=existing.name,
                version=existing.version,
                source="; ".join(sorted(set(existing.source.split("; ") + [spec.source]))),
                scope="; ".join(sorted(set(existing.scope.split("; ") + [spec.scope]))),
            )
    return tuple(sorted(deduped.values(), key=lambda item: (item.name.lower(), item.version, item.scope, item.source)))


def build_spdx_document(root: Path = REPO_ROOT) -> dict[str, object]:
    pyproject = _load_pyproject(root)
    project = pyproject["project"]
    project_name = project["name"]
    project_version = project["version"]
    dependencies = dependency_inventory(root)
    project_spdx_id = f"SPDXRef-Package-{project_name.replace('-', '.')}"

    packages: list[dict[str, object]] = [
        {
            "name": project_name,
            "SPDXID": project_spdx_id,
            "versionInfo": project_version,
            "downloadLocation": "https://github.com/eregular13/MasterBlaster",
            "filesAnalyzed": False,
            "supplier": "NOASSERTION",
        }
    ]
    relationships: list[dict[str, str]] = [
        {
            "spdxElementId": "SPDXRef-DOCUMENT",
            "relationshipType": "DESCRIBES",
            "relatedSpdxElement": project_spdx_id,
        }
    ]

    for spec in dependencies:
        packages.append(
            {
                "name": spec.name,
                "SPDXID": spec.package_spdx_id,
                "versionInfo": spec.version,
                "downloadLocation": "NOASSERTION",
                "filesAnalyzed": False,
                "supplier": "NOASSERTION",
                "externalRefs": [
                    {
                        "referenceCategory": "PACKAGE-MANAGER",
                        "referenceType": "purl",
                        "referenceLocator": f"pkg:pypi/{spec.name.lower()}@{spec.version}",
                    }
                ],
                "annotations": [
                    {
                        "annotationType": "OTHER",
                        "annotator": f"Tool: {TOOL_NAME}-{TOOL_VERSION}",
                        "annotationDate": FIXED_CREATED,
                        "comment": f"source={spec.source}; scope={spec.scope}",
                    }
                ],
            }
        )
        relationships.append(
            {
                "spdxElementId": project_spdx_id,
                "relationshipType": "DEPENDS_ON",
                "relatedSpdxElement": spec.package_spdx_id,
            }
        )

    return {
        "spdxVersion": SPDX_VERSION,
        "dataLicense": "CC0-1.0",
        "SPDXID": "SPDXRef-DOCUMENT",
        "name": "MasterBlaster P0 Dependency SBOM",
        "documentNamespace": f"https://github.com/eregular13/MasterBlaster/spdx/{project_name}-{project_version}",
        "creationInfo": {
            "created": FIXED_CREATED,
            "creators": [f"Tool: {TOOL_NAME}-{TOOL_VERSION}"],
        },
        "documentDescribes": [project_spdx_id],
        "packages": packages,
        "relationships": relationships,
    }


def render_spdx_json(document: dict[str, object]) -> str:
    return json.dumps(document, indent=2, sort_keys=True) + "\n"


def write_sbom(output: Path = DEFAULT_OUTPUT, root: Path = REPO_ROOT) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(render_spdx_json(build_spdx_document(root)), encoding="utf-8")


def check_sbom(output: Path = DEFAULT_OUTPUT, root: Path = REPO_ROOT) -> list[str]:
    expected = render_spdx_json(build_spdx_document(root))
    if not output.exists():
        return [f"{output} does not exist; run python scripts/generate_sbom.py"]
    actual = output.read_text(encoding="utf-8")
    if actual != expected:
        return [f"{output} is stale; run python scripts/generate_sbom.py"]
    return []


def _print_dependencies(dependencies: Iterable[DependencySpec]) -> None:
    for spec in dependencies:
        print(f"{spec.scope}: {spec.name}=={spec.version} ({spec.source})")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate or check the deterministic MasterBlaster SPDX SBOM.")
    parser.add_argument("--check", action="store_true", help="Fail if the checked-in SBOM is stale.")
    parser.add_argument("--list", action="store_true", help="Print the parsed dependency inventory.")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT, help="SBOM output path.")
    args = parser.parse_args(argv)

    if args.list:
        _print_dependencies(dependency_inventory(REPO_ROOT))
        return 0
    if args.check:
        errors = check_sbom(args.output, REPO_ROOT)
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1 if errors else 0
    write_sbom(args.output, REPO_ROOT)
    print(f"Wrote {args.output.relative_to(REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
