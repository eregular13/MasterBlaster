import json
from pathlib import Path

import pytest

from masterblaster_control.p8_auth import LocalAuthStore, LocalUser


def test_default_users_are_seeded(tmp_path):
    store = LocalAuthStore(tmp_path / "users.json")
    users = store.load_users()

    assert {user.user_id for user in users} == {"viewer", "operator", "admin"}
    assert (tmp_path / "users.json").exists()


def test_authenticate_maps_user_to_rbac(tmp_path):
    store = LocalAuthStore(tmp_path / "users.json")
    rbac = store.authenticate("admin")

    assert rbac.principal.user_id == "admin"
    assert rbac.principal.role == "admin"
    assert rbac.allowed("rotate.keys")


def test_authenticate_rejects_unknown_user(tmp_path):
    store = LocalAuthStore(tmp_path / "users.json")

    with pytest.raises(PermissionError, match="Unknown local user"):
        store.authenticate("intruder")


def test_save_and_reload_users(tmp_path):
    store = LocalAuthStore(tmp_path / "users.json")
    store.save_users((LocalUser("auditor", "Auditor", "viewer"),))
    reloaded = store.load_users()

    assert len(reloaded) == 1
    assert reloaded[0].user_id == "auditor"
    payload = json.loads((tmp_path / "users.json").read_text(encoding="utf-8"))
    assert payload["users"][0]["auth_provider"] == "local"