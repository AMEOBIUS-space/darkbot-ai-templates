# Cache Layer

> In-memory cache with TTL, LRU eviction, and Redis-compatible interface

## Features

- TTL-based expiry (per-key and default)
- LRU eviction (max_size + max_memory)
- Redis-compatible commands: set, get, delete, exists, expire, incr, mget, mset, keys, flush
- Glob pattern key matching
- Expired entry cleanup
- Thread-safe (RLock)
- Statistics (hits, misses, hit_rate, evictions, sets, memory)
- INFO command (Redis-like)

## Quick Start

```python
from cache import CacheLayer

cache = CacheLayer(max_size=1000, default_ttl=300)
cache.set("user:1", {"name": "Alice"}, ttl=60)
user = cache.get("user:1")
cache.incr("page_views")
print(cache.stats())
```

## Tests

```bash
python -m pytest tests/ -v
```

## License

MIT

Freelance portfolio: [https://ameobius-space.github.io/kwork-portfolio/](https://ameobius-space.github.io/kwork-portfolio/)
