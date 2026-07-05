import sys, os, time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from key_manager import APIKeyManager, APIKey


def test_create_key():
    mgr = APIKeyManager()
    raw, key = mgr.create_key(scopes=["read", "write"])
    assert raw.startswith("dk_")
    assert len(raw) > 20
    assert "read" in key.scopes
    assert "write" in key.scopes


def test_validate_key_valid():
    mgr = APIKeyManager()
    raw, key = mgr.create_key()
    valid, returned_key, msg = mgr.validate_key(raw)
    assert valid is True
    assert returned_key is not None
    assert msg == "OK"


def test_validate_key_invalid_format():
    mgr = APIKeyManager()
    valid, _, msg = mgr.validate_key("invalid_key")
    assert valid is False
    assert "format" in msg


def test_validate_key_not_found():
    mgr = APIKeyManager()
    valid, _, msg = mgr.validate_key("dk_" + "a" * 64)
    assert valid is False
    assert "not found" in msg


def test_validate_key_revoked():
    mgr = APIKeyManager()
    raw, key = mgr.create_key()
    mgr.revoke_key(key.key_id)
    valid, _, msg = mgr.validate_key(raw)
    assert valid is False
    assert "revoked" in msg


def test_check_scope():
    mgr = APIKeyManager()
    _, key = mgr.create_key(scopes=["read", "write"])
    assert mgr.check_scope(key, "read")
    assert mgr.check_scope(key, "write")
    assert not mgr.check_scope(key, "admin")


def test_check_scope_admin_override():
    mgr = APIKeyManager()
    _, key = mgr.create_key(scopes=["admin"])
    assert mgr.check_scope(key, "read")
    assert mgr.check_scope(key, "write")
    assert mgr.check_scope(key, "delete")


def test_rotate_key():
    mgr = APIKeyManager()
    raw1, key1 = mgr.create_key()
    raw2, key2 = mgr.rotate_key(key1.key_id)
    assert raw1 != raw2
    valid1, _, _ = mgr.validate_key(raw1)
    assert not valid1  # Old key revoked
    valid2, _, _ = mgr.validate_key(raw2)
    assert valid2  # New key valid


def test_revoke_key():
    mgr = APIKeyManager()
    _, key = mgr.create_key()
    assert mgr.revoke_key(key.key_id)
    assert not mgr.revoke_key("nonexistent")


def test_list_keys():
    mgr = APIKeyManager()
    mgr.create_key(scopes=["read"], description="App1")
    mgr.create_key(scopes=["admin"], description="App2")
    keys = mgr.list_keys()
    assert len(keys) == 2
    assert "..." in keys[0]["key_id"]  # Truncated


def test_stats():
    mgr = APIKeyManager()
    mgr.create_key()
    mgr.create_key()
    mgr.revoke_key(list(mgr.keys.keys())[0])
    stats = mgr.stats()
    assert stats["total_keys"] == 2
    assert stats["active"] == 1
    assert stats["revoked"] == 1


def test_cleanup_expired():
    mgr = APIKeyManager()
    mgr.create_key(expiry_days=-1)  # Already expired
    mgr.create_key(expiry_days=30)  # Valid
    removed = mgr.cleanup_expired()
    assert removed == 1


def test_usage_count():
    mgr = APIKeyManager()
    raw, _ = mgr.create_key()
    mgr.validate_key(raw)
    mgr.validate_key(raw)
    key = list(mgr.keys.values())[0]
    assert key.usage_count == 2
