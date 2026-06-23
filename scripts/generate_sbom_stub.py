from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]


def _read_requirements(path: Path) -> list[tuple[str, str]]:
    components: list[tuple[str, str]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        value = line.strip()
        if not value or value.startswith("#"):
            continue
        if "==" in value:
            name, version = value.split("==", 1)
            components.append((name.strip(), version.strip()))
        else:
            components.append((value, "unspecified"))
    return components


def build_sbom(requirements_path: Path) -> dict[str, object]:
    now = datetime.now(timezone.utc).isoformat()
    components = _read_requirements(requirements_path)
    return {
        "bomFormat": "CycloneDX",
        "specVersion": "1.5",
        "serialNumber": "urn:uuid:masterblaster-p0-sbom-stub",
        "version": 1,
        "metadata": {
            "timestamp": now,
            "component": {
                "type": "application",
                "name": "masterblaster-control",
                "version": "0.2.0",
                "description": "MasterBlaster P0 authorized assessment simulator",
            },
            "properties": [
                {"name": "p0:simulator-only", "value": "true"},
                {"name": "p0:network-transport", "value": "false"},
            ],
        },
        "components": [
            {
                "type": "library",
                "name": name,
                "version": version,
                "purl": f"pkg:pypi/{name}@{version}",
            }
            for name, version in components
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate a CycloneDX SBOM stub for P0 dependencies.")
    parser.add_argument(
        "--output",
        default=str(REPO_ROOT / "dist" / "sbom.cdx.json"),
        help="Output path for the SBOM JSON file.",
    )
    args = parser.parse_args()

    requirements = REPO_ROOT / "requirements.txt"
    if not requirements.exists():
        print(f"Missing requirements file: {requirements}", file=sys.stderr)
        return 1

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    payload = build_sbom(requirements)
    output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"Wrote SBOM stub with {len(payload['components'])} component(s) to {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())