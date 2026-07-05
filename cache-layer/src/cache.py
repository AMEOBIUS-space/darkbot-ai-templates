"""Cache Layer — in-memory cache with TTL, LRU eviction, and Redis-compatible interface."""
import time
import threading
import json
import hashlib
import pickle
from typing import Dict, List, Optional, Any, Tuple, Callable
from dataclasses import dataclass, field
from collections import OrderedDict
from datetime import datetime


@dataclass
class CacheEntry:
    key: str
    value: Any
    created_at: float
    ttl: float  # seconds, 0 = no expiry
    access_count: int = 0
    last_accessed: float = 0.0
    size: int = 0  # approximate size in bytes

    def is_expired(self) -> bool:
        if self.ttl == 0:
            return False
        return time.time() - self.created_at > self.ttl

    def touch(self):
        self.access_count += 1
        self.last_accessed = time.time()


class CacheLayer:
    """In-memory cache with TTL and LRU eviction."""

    def __init__(self, max_size: int = 1000, max_memory_mb: float = 100.0,
                 default_ttl: float = 300.0):
        self.max_size = max_size
        self.max_memory = max_memory_mb * 1024 * 1024
        self.default_ttl = default_ttl
        self._store: OrderedDict[str, CacheEntry] = OrderedDict()
        self._lock = threading.RLock()
        self._hits = 0
        self._misses = 0
        self._evictions = 0
        self._sets = 0
        self._current_memory = 0

    def _estimate_size(self, value: Any) -> int:
        try:
            return len(pickle.dumps(value))
        except Exception:
            return 100  # Fallback estimate

    def set(self, key: str, value: Any, ttl: float = None) -> bool:
        """Set a cache entry. Returns True if set."""
        with self._lock:
            ttl = ttl if ttl is not None else self.default_ttl
            size = self._estimate_size(value)

            # Remove existing entry if present
            if key in self._store:
                old = self._store[key]
                self._current_memory -= old.size
                del self._store[key]

            # Evict if over capacity
            while (len(self._store) >= self.max_size or
                   self._current_memory + size > self.max_memory) and self._store:
                self._evict_lru()

            entry = CacheEntry(
                key=key, value=value, created_at=time.time(),
                ttl=ttl, size=size, last_accessed=time.time(),
            )
            self._store[key] = entry
            self._current_memory += size
            self._sets += 1
            return True

    def get(self, key: str, default: Any = None) -> Any:
        """Get a value from cache. Returns default if not found or expired."""
        with self._lock:
            if key not in self._store:
                self._misses += 1
                return default

            entry = self._store[key]
            if entry.is_expired():
                self._current_memory -= entry.size
                del self._store[key]
                self._misses += 1
                return default

            entry.touch()
            self._hits += 1
            # Move to end (most recently used)
            self._store.move_to_end(key)
            return entry.value

    def delete(self, key: str) -> bool:
        """Delete a key from cache."""
        with self._lock:
            if key in self._store:
                entry = self._store[key]
                self._current_memory -= entry.size
                del self._store[key]
                return True
            return False

    def exists(self, key: str) -> bool:
        """Check if key exists and is not expired."""
        with self._lock:
            if key not in self._store:
                return False
            if self._store[key].is_expired():
                self._current_memory -= self._store[key].size
                del self._store[key]
                return False
            return True

    def expire(self, key: str, ttl: float) -> bool:
        """Set TTL on existing key."""
        with self._lock:
            if key in self._store:
                self._store[key].ttl = ttl
                self._store[key].created_at = time.time()
                return True
            return False

    def incr(self, key: str, amount: int = 1, ttl: float = None) -> int:
        """Increment a numeric value. Creates if not exists."""
        with self._lock:
            current = self.get(key, 0)
            new_value = current + amount
            self.set(key, new_value, ttl)
            return new_value

    def mget(self, keys: List[str]) -> List[Any]:
        """Get multiple values."""
        return [self.get(k) for k in keys]

    def mset(self, mapping: Dict[str, Any], ttl: float = None) -> bool:
        """Set multiple values."""
        for k, v in mapping.items():
            self.set(k, v, ttl)
        return True

    def keys(self, pattern: str = "*") -> List[str]:
        """Get keys matching a glob pattern."""
        import fnmatch
        with self._lock:
            return [k for k in self._store.keys() if fnmatch.fnmatch(k, pattern)]

    def flush(self) -> int:
        """Clear all entries. Returns count cleared."""
        with self._lock:
            count = len(self._store)
            self._store.clear()
            self._current_memory = 0
            return count

    def _evict_lru(self):
        """Evict least recently used entry."""
        if not self._store:
            return
        # First entry is LRU (OrderedDict maintains insertion/access order)
        key, entry = self._store.popitem(last=False)
        self._current_memory -= entry.size
        self._evictions += 1

    def cleanup_expired(self) -> int:
        """Remove all expired entries. Returns count removed."""
        with self._lock:
            expired = [k for k, e in self._store.items() if e.is_expired()]
            for k in expired:
                self._current_memory -= self._store[k].size
                del self._store[k]
            return len(expired)

    def stats(self) -> Dict:
        """Get cache statistics."""
        total = self._hits + self._misses
        return {
            "entries": len(self._store),
            "hits": self._hits,
            "misses": self._misses,
            "hit_rate": f"{self._hits / total * 100:.1f}%" if total > 0 else "0%",
            "evictions": self._evictions,
            "sets": self._sets,
            "memory_mb": round(self._current_memory / 1024 / 1024, 2),
            "max_size": self.max_size,
            "max_memory_mb": round(self.max_memory / 1024 / 1024, 2),
        }

    def info(self) -> Dict:
        """Redis-like INFO command."""
        return {
            "version": "1.0.0",
            "entries": len(self._store),
            "memory_used": self._current_memory,
            "stats": self.stats(),
        }
