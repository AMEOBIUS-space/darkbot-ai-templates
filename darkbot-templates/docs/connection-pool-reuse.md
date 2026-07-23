# Connection Pool: Reuse Expensive Resources

> Part of the [darkbot-templates](https://github.com/AMEOBIUS-space/darkbot-ai-templates) series — zero-dependency production templates.

Opening a database connection costs 50-200ms. Closing it costs another round-trip. If you open/close per request, you're spending more time on handshake than on actual work. A connection pool keeps connections warm and hands them out cheaply.

## Usage

```python
import sqlite3
from darkbot_templates.templates.connection_pool import ConnectionPool

pool = ConnectionPool(
    factory=lambda: sqlite3.connect("app.db"),
    destroyer=lambda c: c.close(),
    min_size=2,
    max_size=10,
    max_lifetime=3600,     # recycle connections after 1 hour
    idle_timeout=300,       # close idle connections after 5 min
    acquire_timeout=10,     # wait up to 10s for a free connection
)

# Use as context manager
with pool.acquire() as conn:
    rows = conn.execute("SELECT * FROM users").fetchall()
    # connection auto-returned to pool on exit
```

## How It Works

```
[free pool] ──acquire()──▶ [caller uses conn] ──__exit__──▶ [free pool]
     │                                                         │
     └─── min_size maintained ────── health check ─────────────┘
```

1. `acquire()` pops from the free queue (or blocks up to `acquire_timeout`)
2. If pool is below `min_size`, new connections are created eagerly
3. If pool is at `max_size`, caller blocks until one is returned
4. `__exit__` returns the connection; if an exception occurred, it's marked unhealthy
5. Background health checks replace stale/unhealthy connections

## Health Check

```python
pool = ConnectionPool(
    factory=lambda: psycopg2.connect(DSN),
    destroyer=lambda c: c.close(),
    health_check=lambda c: c.cursor().execute("SELECT 1") or True,
    min_size=2,
    max_size=10,
)

# Before handing out a connection, pool checks health_check()
# Failed → connection destroyed → new one created
```

## Connection Lifecycle

| Phase | What Happens | Configured By |
|-------|-------------|---------------|
| Creation | `factory()` called | `min_size`, `max_size` |
| Active | Caller holds via `acquire()` | `acquire_timeout` |
| Return | Back to free queue | Automatic on `__exit__` |
| Idle | Sitting in free queue | `idle_timeout` |
| Expired | Age exceeds lifetime | `max_lifetime` |
| Unhealthy | Exception during use or health check fails | Auto-replaced |

## Thread Safety

The pool uses a `threading.Lock` + `Queue` internally. Multiple threads can call `acquire()` concurrently — the first to dequeue wins, others block.

```python
import threading

pool = ConnectionPool(factory=make_conn, min_size=5, max_size=20)

def worker(task_id):
    with pool.acquire() as conn:
        conn.execute(f"INSERT INTO logs VALUES ({task_id})")

threads = [threading.Thread(target=worker, args=(i,)) for i in range(50)]
for t in threads: t.start()
for t in threads: t.join()

print(pool.stats)
# {"created": 20, "active": 0, "idle": 20, "max_size": 20, "acquired_total": 50}
```

## Pairing with Circuit Breaker

```python
from darkbot_templates.templates.connection_pool import ConnectionPool
from darkbot_templates.templates.circuit_breaker import CircuitBreaker

pool = ConnectionPool(factory=db_connect, min_size=2, max_size=10)
cb = CircuitBreaker(failure_threshold=5, recovery_timeout=60.0)

def query(sql):
    if not cb.allow():
        raise Exception("circuit open — database unavailable")
    with pool.acquire() as conn:
        try:
            result = conn.execute(sql).fetchall()
            cb.success()
            return result
        except Exception:
            cb.failure()
            raise
```

## Testing

```bash
pytest tests/test_connection_pool.py -v
```

## References

- [HikariCP](https://github.com/brettwooldridge/HikariCP) — JDBC pool that popularized max-lifetime recycling
- [SQLAlchemy Pooling](https://docs.sqlalchemy.org/en/20/core/pooling.html)

---

*darkbot-templates v1.8.5 — 30 templates, zero dependencies, 448 tests.*
