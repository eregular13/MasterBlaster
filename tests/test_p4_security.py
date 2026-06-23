from pathlib import Path

from masterblaster_control.p4_security import KeyStore, Principal, RBAC, export_audit_filtered


def test_keystore_persists_signing_key(tmp_path):
    path = tmp_path / "signing_key.bin"
    first = KeyStore(path)
    key_a = first.load_or_create()
    second = KeyStore(path)
    key_b = second.load_or_create()
    assert key_a == key_b
    rotated = second.rotate()
    assert rotated != key_a


def test_rbac_enforces_permissions():
    viewer = RBAC(Principal(user_id="v", role="viewer"))
    admin = RBAC(Principal(user_id="a", role="admin"))
    assert viewer.allowed("read.audit")
    assert not viewer.allowed("apply.retention")
    assert admin.allowed("apply.retention")


def test_filtered_audit_export():
    events = [
        {"tenant_id": "t1", "engagement_id": "e1", "action": "runner.completed", "reason_code": "ALLOW"},
        {"tenant_id": "t2", "engagement_id": "e2", "action": "runner.denied", "reason_code": "DENY"},
    ]
    exported = export_audit_filtered(events, tenant_id="t1", action="runner.completed")
    assert "t1" in exported
    assert "t2" not in exported