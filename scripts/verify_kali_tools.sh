#!/bin/bash
set -euo pipefail

echo "=== Validate MasterBlaster P0 Manifests ==="
python - <<'PY'
from masterblaster_control.runner_simulator import MANIFESTS

for adapter_id, manifest in MANIFESTS.items():
    if not manifest.reviewed:
        raise SystemExit(f"{adapter_id} is not reviewed")
    if manifest.network_access:
        raise SystemExit(f"{adapter_id} unexpectedly declares network access")
    print(f"OK {adapter_id} {manifest.version} {manifest.execution_mode}")

print(f"Validated {len(MANIFESTS)} reviewed manifest(s).")
PY
