# Circuit Breaker Pattern in Pure Python

> Part of the [darkbot-templates](https://github.com/AMEOBIUS-space/darkbot-ai-templates) series — zero-dependency production templates.

When a downstream service (database, API, cache) starts failing, hammering it with retries makes things worse. The **circuit breaker** pattern stops the bleeding: after N consecutive failures, "trip" the circuit and fail-fast instead of queuing up more doomed requests.

## The Three States

```
CLOSED ──(failures ≥ threshold)──▶ OPEN
   ▲                                  │
   │                                  │ (after recovery_timeout)
   │                                  ▼
   └──(success)──── HALF_OPEN ◀──────
```

- **CLOSED** — normal operation. Every request goes through. Failures increment a counter.
- **OPEN** — tripped. Requests are rejected immediately (fail-fast). No calls to downstream at all.
- **HALF_OPEN** — probe mode. After `recovery_timeout` seconds, let one request through. If it succeeds → CLOSED. If it fails → back to OPEN.

## Usage

```python
from darkbot_templates.templates.circuit_breaker import CircuitBreaker

cb = CircuitBreaker(failure_threshold=5, recovery_timeout=30.0)

def fetch_user(user_id):
    if not cb.allow():
        return None  # circuit is OPEN — fail fast

    try:
        resp = http_client.get(f"/users/{user_id}")
        resp.raise_for_status()
        cb.success()
        return resp.json()
    except Exception:
        cb.failure()
        return None
```

That's it. No decorators, no async ceremony — just a state machine you check before every call.

## When to Use It

| Scenario | Use Circuit Breaker? |
|----------|---------------------|
| External HTTP API with latency spikes | Yes — trip after 5 failures, recover after 30s |
| Database connection drops | Yes — fail-fast instead of piling up timeouts |
| In-process function call | No — no network, no recovery needed |
| Batch one-shot job | No — let it fail and retry the whole batch |

## Thread Safety

The template uses `threading.Lock` internally — safe to share one `CircuitBreaker` instance across threads:

```python
cb = CircuitBreaker(failure_threshold=10, recovery_timeout=60.0)

# Thread 1
cb.allow()   # → True
cb.failure()

# Thread 2 (concurrent)
cb.allow()   # → state check is locked, consistent
```

## Combining with Retry Queue

The circuit breaker pairs naturally with the `retry_queue` template. Breaker protects the hot path; retry queue handles the deferred recovery:

```python
from darkbot_templates.templates.circuit_breaker import CircuitBreaker
from darkbot_templates.templates.retry_queue import RetryQueue

cb = CircuitBreaker(failure_threshold=5, recovery_timeout=30.0)
rq = RetryQueue(max_retries=3, base_delay=1.0)

def call_api(endpoint):
    if not cb.allow():
        rq.enqueue(endpoint)  # defer for later
        return None
    try:
        result = http_client.get(endpoint)
        cb.success()
        return result
    except Exception:
        cb.failure()
        rq.enqueue(endpoint)
        return None
```

## Testing

```bash
pytest tests/test_new_resilience.py -k circuit -v
```

All circuit breaker tests pass as part of the 448-test suite.

## References

- [Martin Fowler — CircuitBreaker](https://martinfowler.com/bliki/CircuitBreaker.html)
- [Netflix Hystrix](https://github.com/Netflix/Hystrix/wiki/How-it-Works) — the pattern that popularized it
- ISO 30116 style resilience patterns

---

*darkbot-templates v1.8.5 — 30 templates, zero dependencies, 448 tests.*
