from masterblaster_control.p9_hsm_keystore import ExternalHSMKeyStore, HSMKeyReference


def test_hsm_falls_back_without_feature_flag(tmp_path):
    fallback_path = tmp_path / "signing_key.bin"
    store = ExternalHSMKeyStore(
        reference=HSMKeyReference(provider="test", key_id="k1", path=str(tmp_path / "missing.bin")),
        fallback=__import__("masterblaster_control.p4_security", fromlist=["KeyStore"]).KeyStore(fallback_path),
    )
    key = store.load_signing_key()
    assert len(key) == 32
    assert "Feature enabled" in store.status_markdown()