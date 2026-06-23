from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from masterblaster_control.p0_resources import list_resources
from masterblaster_control.runner_simulator import MANIFESTS


def main() -> int:
    print("=== Validate MasterBlaster P0 Registry ===")

    for adapter_id, manifest in MANIFESTS.items():
        if not manifest.reviewed:
            raise SystemExit(f"{adapter_id} is not reviewed")
        if manifest.network_access:
            raise SystemExit(f"{adapter_id} unexpectedly declares network access")
        print(f"OK manifest {adapter_id} {manifest.version} {manifest.execution_mode}")

    resources = list_resources()
    for resource in resources:
        if not resource.non_executing:
            raise SystemExit(f"{resource.uri} is not marked non-executing")
        print(f"OK resource {resource.uri} {resource.version} non-executing")

    print(f"Validated {len(MANIFESTS)} reviewed manifest(s).")
    print(f"Validated {len(resources)} non-executing resource(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
