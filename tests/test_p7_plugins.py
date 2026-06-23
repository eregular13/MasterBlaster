import json
from pathlib import Path

import pytest

from masterblaster_control.p7_plugins import (
    PluginLoadError,
    PluginRegistry,
    discover_plugins,
    load_plugin_manifest,
    reload_plugins,
    set_plugin_dev_mode,
)


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


def test_hot_reload_picks_up_new_manifest(tmp_path):
    first_dir = tmp_path / "plugin-a"
    first_dir.mkdir()
    first_dir.joinpath("plugin.json").write_text(
        json.dumps(
            {
                "schema_version": "1.0",
                "plugin_id": "plugin.alpha",
                "name": "Alpha",
                "version": "1.0.0",
                "min_core_version": "1.0.0",
                "reviewed": True,
                "non_executing": True,
            }
        ),
        encoding="utf-8",
    )
    registry = PluginRegistry(tmp_path)
    assert len(registry.discover()) == 1

    second_dir = tmp_path / "plugin-b"
    second_dir.mkdir()
    second_dir.joinpath("plugin.json").write_text(
        json.dumps(
            {
                "schema_version": "1.0",
                "plugin_id": "plugin.beta",
                "name": "Beta",
                "version": "1.0.0",
                "min_core_version": "1.0.0",
                "reviewed": True,
                "non_executing": True,
            }
        ),
        encoding="utf-8",
    )
    reloaded = registry.hot_reload()
    assert {plugin.plugin_id for plugin in reloaded} == {"plugin.alpha", "plugin.beta"}


def test_reload_plugins_uses_registry(tmp_path):
    plugin_dir = tmp_path / "plugin-a"
    plugin_dir.mkdir()
    plugin_dir.joinpath("plugin.json").write_text(
        json.dumps(
            {
                "schema_version": "1.0",
                "plugin_id": "plugin.reload",
                "name": "Reload",
                "version": "1.0.0",
                "min_core_version": "1.0.0",
                "reviewed": True,
                "non_executing": True,
            }
        ),
        encoding="utf-8",
    )
    set_plugin_dev_mode(True, tmp_path)
    plugins = reload_plugins(tmp_path)
    assert len(plugins) == 1