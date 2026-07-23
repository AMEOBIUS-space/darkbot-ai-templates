# Cache Manager: TTL + LRU Without Redis

> Part of the [darkbot-templates](https://github.com/AMEOBIUS-space/darkbot-ai-templates) series — zero-dependency production templates.

Not every cache needs Redis. For single-process apps, test suites, and CLI tools, an in-memory cache with TTL and LRU eviction is enough — and it's 1000x faster.

## Usage

```python
from darkbot_templates.templates.cache_manager import CacheManager

cache = CacheManager(max_size=1000, default_ttl=300)

# Set
cache.set("user:42", {"name": "Alice", "role": "admin"})

# Get
user = cache.get("user:42")
# → {"name": "Alice", "role": "admin"}

# After 300 seconds, the entry expires automatically
```

## Per-Key TTL

Override the default TTL for specific keys:

```python
cache.set("session:abc", token, ttl=3600)      # 1 hour
cache.set("otp:xyz", code, ttl=120)              # 2 minutes
cache.set("config", settings, ttl=0)             # 0 = no expiry (permanent)
```

## Tag-Based Invalidation

Group related keys and invalidate them together:

```python
cache.set("user:42:profile", profile, tags=["user_42"])
cache.set("user:42:settings", settings, tags=["user_42"])
cache.set("user:42:sessions", sessions, tags=["user_42"])

# User updates profile — invalidate all their cached data
cache.invalidate_tag("user_42")
# → Removes all 3 entries
```

## LRU Eviction

When the cache reaches `max_size`, the least-recently-used entry is evicted:

```python
cache = CacheManager(max_size=3)

cache.set("a", 1)
cache.set("b", 2)
cache.set("c", 3)
cache.get("a")        # "a" is now most recently used
cache.set("d", 4)     # evicts "b" (least recently used)

print(cache.get("b")) # → None (evicted)
print(cache.get("a")) # → 1 (still here)
```

## Function Caching Decorator

```python
cache = CacheManager(max_size=500, default_ttl=600)

@cache.cached(ttl=120)
def fetch_user(user_id):
    # Expensive DB/API call
    return db.query(f"SELECT * FROM users WHERE id = {user_id}")

# First call: executes and caches
fetch_user(42)

# Second call: returns from cache
fetch_user(42)

# Check stats
print(cache.stats)
# {"hits": 1, "misses": 1, "evictions": 0, "sets": 1, "deletes": 0, "size": 1}
```

## Thread Safety

All operations use `threading.RLock`. Safe to share one cache instance across threads.

## Testing

```bash
pytest tests/test_cache_manager.py -v
```

## References

- [Redis TTL + LRU](https://redis.io/docs/manual/eviction/)
- [Python functools.lru_cache](https://docs.python.org/3/library/functools.html#functools.lru_cache)

---

*darkbot-templates v1.8.5 — 30 templates, zero dependencies, 448 tests.*
