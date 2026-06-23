import json

from masterblaster_control.p9_feature_flags import feature_flags_markdown, is_feature_enabled, load_feature_flags


def test_default_flags_disable_live_features():
    flags = {flag.name: flag.enabled for flag in load_feature_flags()}
    assert flags["a7_live_adapter"] is False
    assert flags["oidc_auth"] is False
    assert flags["mcp_http"] is True


def test_file_override(tmp_path):
    config = tmp_path / "feature_flags.json"
    config.write_text(json.dumps({"flags": {"a7_live_adapter": True}}), encoding="utf-8")
    assert is_feature_enabled("a7_live_adapter", config) is True


def test_feature_flags_markdown_renders():
    md = feature_flags_markdown()
    assert "a7_live_adapter" in md
    assert "| Flag |" in md