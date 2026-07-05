import sys, os, time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from cache import CacheLayer


def test_set_get():
    c = CacheLayer(default_ttl=10)
    c.set("key1", "value1")
    assert c.get("key1") == "value1"


def test_get_missing():
    c = CacheLayer()
    assert c.get("nonexistent") is None
    assert c.get("nonexistent", "default") == "default"


def test_ttl_expiry():
    c = CacheLayer(default_ttl=0.1)
    c.set("temp", "data")
    time.sleep(0.15)
    assert c.get("temp") is None


def test_no_ttl():
    c = CacheLayer(default_ttl=0)
    c.set("permanent", "data")
    time.sleep(0.1)
    assert c.get("permanent") == "data"


def test_delete():
    c = CacheLayer()
    c.set("key", "value")
    assert c.delete("key") is True
    assert c.get("key") is None
    assert c.delete("nonexistent") is False


def test_exists():
    c = CacheLayer()
    c.set("key", "value")
    assert c.exists("key") is True
    assert c.exists("missing") is False


def test_expire():
    c = CacheLayer(default_ttl=100)
    c.set("key", "value")
    assert c.expire("key", 0.1) is True
    time.sleep(0.15)
    assert c.get("key") is None


def test_incr():
    c = CacheLayer()
    assert c.incr("counter") == 1
    assert c.incr("counter") == 2
    assert c.incr("counter", 5) == 7


def test_mget():
    c = CacheLayer()
    c.set("a", 1)
    c.set("b", 2)
    c.set("c", 3)
    results = c.mget(["a", "b", "c", "d"])
    assert results == [1, 2, 3, None]


def test_mset():
    c = CacheLayer()
    c.mset({"x": 10, "y": 20, "z": 30})
    assert c.get("x") == 10
    assert c.get("y") == 20
    assert c.get("z") == 30


def test_keys_pattern():
    c = CacheLayer()
    c.set("user:1", "alice")
    c.set("user:2", "bob")
    c.set("post:1", "hello")
    keys = c.keys("user:*")
    assert "user:1" in keys
    assert "user:2" in keys
    assert "post:1" not in keys


def test_flush():
    c = CacheLayer()
    c.set("a", 1)
    c.set("b", 2)
    count = c.flush()
    assert count == 2
    assert len(c._store) == 0


def test_lru_eviction():
    c = CacheLayer(max_size=3)
    c.set("a", 1)
    c.set("b", 2)
    c.set("c", 3)
    # Access "a" to make it recently used
    c.get("a")
    # Add "d" — should evict "b" (least recently used)
    c.set("d", 4)
    assert c.get("a") == 1  # Still exists
    assert c.get("b") is None  # Evicted
    assert c.get("d") == 4


def test_cleanup_expired():
    c = CacheLayer(default_ttl=0.1)
    c.set("a", 1)
    c.set("b", 2)
    c.set("c", 3, ttl=100)  # Long TTL
    time.sleep(0.15)
    removed = c.cleanup_expired()
    assert removed == 2
    assert c.get("c") == 3  # Still exists


def test_stats():
    c = CacheLayer()
    c.set("a", 1)
    c.get("a")  # Hit
    c.get("b")  # Miss
    stats = c.stats()
    assert stats["hits"] == 1
    assert stats["misses"] == 1
    assert stats["entries"] == 1


def test_info():
    c = CacheLayer()
    c.set("key", "value")
    info = c.info()
    assert info["version"] == "1.0.0"
    assert info["entries"] == 1


def test_overwrite():
    c = CacheLayer()
    c.set("key", "old")
    c.set("key", "new")
    assert c.get("key") == "new"


def test_hit_rate():
    c = CacheLayer()
    c.set("a", 1)
    c.get("a")  # Hit
    c.get("a")  # Hit
    c.get("b")  # Miss
    stats = c.stats()
    assert "66.7%" in stats["hit_rate"]
