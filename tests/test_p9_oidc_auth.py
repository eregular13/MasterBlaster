import pytest

from masterblaster_control.p9_oidc_auth import OIDCAuthStore


def test_oidc_scaffold_seeds_config(tmp_path):
    store = OIDCAuthStore(tmp_path / "oidc.json")
    config = store.load_config()
    assert "authorize" in config.authorization_url()
    assert "OIDC Auth Scaffold" in store.scaffold_markdown()


def test_oidc_authenticate_requires_feature_flag(tmp_path):
    store = OIDCAuthStore(tmp_path / "oidc.json")
    with pytest.raises(PermissionError, match="OIDC auth feature flag is disabled"):
        store.authenticate_claims({"sub": "user-1"})