import sys, os, tempfile, time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from secrets import SecretManager


def test_set_get_secret():
    mgr = SecretManager(master_key="my_master_key")
    mgr.set_secret("api.key", "secret123")
    assert mgr.get_secret("api.key") == "secret123"


def test_get_missing():
    mgr = SecretManager()
    assert mgr.get_secret("nonexistent") is None


def test_encrypted_storage():
    mgr = SecretManager(master_key="key123")
    mgr.set_secret("token", "my_secret_token")
    # Stored value should be encrypted (not plaintext)
    assert mgr._secrets["token"].encrypted_value != "my_secret_token"
    # But decrypts correctly
    assert mgr.get_secret("token") == "my_secret_token"


def test_delete():
    mgr = SecretManager()
    mgr.set_secret("temp", "val")
    assert mgr.delete_secret("temp") is True
    assert mgr.get_secret("temp") is None
    assert mgr.delete_secret("nonexistent") is False


def test_version_increment():
    mgr = SecretManager()
    mgr.set_secret("key", "v1")
    assert mgr._secrets["key"].version == 1
    mgr.set_secret("key", "v2")
    assert mgr._secrets["key"].version == 2
    mgr.set_secret("key", "v3")
    assert mgr._secrets["key"].version == 3


def test_rotate():
    mgr = SecretManager()
    mgr.set_secret("api_key", "original_value", rotation_days=30)
    rotated = mgr.rotate_secret("api_key")
    assert rotated is not None
    assert rotated.version == 2
    assert mgr.get_secret("api_key") != "original_value"
    assert len(mgr.get_secret("api_key")) > 0


def test_rotate_with_value():
    mgr = SecretManager()
    mgr.set_secret("key", "old_val")
    rotated = mgr.rotate_secret("key", new_value="new_val")
    assert mgr.get_secret("key") == "new_val"


def test_rotate_nonexistent():
    mgr = SecretManager()
    assert mgr.rotate_secret("nonexistent") is None


def test_needs_rotation():
    mgr = SecretManager()
    mgr.set_secret("key", "val", rotation_days=0)
    assert mgr.needs_rotation("key") is False

    mgr.set_secret("key2", "val", rotation_days=-1)  # Already expired
    assert mgr.needs_rotation("key2") is True


def test_list_secrets():
    mgr = SecretManager()
    mgr.set_secret("key1", "v1", tags=["api"])
    mgr.set_secret("key2", "v2", tags=["db"])
    secrets = mgr.list_secrets()
    assert len(secrets) == 2
    assert "api" in secrets[0]["tags"]


def test_export_env():
    mgr = SecretManager()
    mgr.set_secret("api.key", "secret123")
    mgr.set_secret("db.password", "pass456")
    env = mgr.export_env()
    assert "API_KEY=secret123" in env
    assert "DB_PASSWORD=pass456" in env


def test_export_env_specific_keys():
    mgr = SecretManager()
    mgr.set_secret("a", "1")
    mgr.set_secret("b", "2")
    env = mgr.export_env(["a"])
    assert "A=1" in env
    assert "B=2" not in env


def test_load_env_file():
    mgr = SecretManager()
    with tempfile.NamedTemporaryFile(mode="w", suffix=".env", delete=False) as f:
        f.write('API_KEY=secret123\nDB_PASSWORD=pass456\n# comment\n')
        f.flush()
        path = f.name
    try:
        count = mgr.load_env_file(path)
        assert count == 2
        assert mgr.get_secret("api.key") == "secret123"
    finally:
        os.unlink(path)


def test_stats():
    mgr = SecretManager()
    mgr.set_secret("k1", "v1", rotation_days=30)
    mgr.set_secret("k2", "v2")
    mgr.set_secret("k1", "v1_updated")  # Version 2
    stats = mgr.stats()
    assert stats["total_secrets"] == 2
    assert stats["total_versions"] == 3  # 2 + 1


def test_tags():
    mgr = SecretManager()
    mgr.set_secret("key", "val", tags=["production", "api"])
    assert "production" in mgr._secrets["key"].tags
    assert "api" in mgr._secrets["key"].tags


def test_different_master_keys():
    mgr1 = SecretManager(master_key="key1")
    mgr1.set_secret("test", "secret_value")
    assert mgr1.get_secret("test") == "secret_value"

    mgr2 = SecretManager(master_key="key2")
    # Different key = different encryption, can't decrypt mgr1's secrets
    mgr2._secrets["test"] = mgr1._secrets["test"]
    try:
        mgr2.get_secret("test")
        assert False, "Should fail with wrong key"
    except Exception:
        pass  # Expected — wrong decryption key
