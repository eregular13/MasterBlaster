import json
from pathlib import Path

import pytest

from masterblaster_control.p7_plugins import PluginLoadError, discover_plugins, load_plugin_manifest


def test_discover_builtin_plugins():
    plugins = discover_plugins(Path("plugins"))
    ids = {plugin.plugin_id for plugin in plugins}
    assert "plugin.builtin.reporting" in ids
    assert "plugin.fixture.observatory" in ids
    assert all(plugin.non_executing for plugin in plugins)
    assert all(plugin.reviewed for plugin in plugins)


def test_plugin_loader_rejects_unreviewed(tmp_path):
    manifest = tmp_path / "plugin.json"
    manifest.write_text(
        json.dumps(
            {
                "schema_version": "1.0",
                "plugin_id": "plugin.evil",
                "name": "Evil",
                "version": "0.0.1",
                "min_core_version": "1.0.0",
                "reviewed": False,
                "non_executing": True,
            }
        ),
        encoding="utf-8",
    )
    with pytest.raises(PluginLoadError):
        load_plugin_manifest(manifest)