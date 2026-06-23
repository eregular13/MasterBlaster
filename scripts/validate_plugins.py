from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from masterblaster_control.p7_plugins import discover_plugins, plugin_catalog_markdown


def main() -> int:
    print("=== Validate MasterBlaster Plugins ===")
    plugins = discover_plugins(REPO_ROOT / "plugins")
    for plugin in plugins:
        print(f"OK {plugin.plugin_id} {plugin.version} non-executing={plugin.non_executing}")
    print(plugin_catalog_markdown(plugins))
    print(f"Validated {len(plugins)} plugin manifest(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())