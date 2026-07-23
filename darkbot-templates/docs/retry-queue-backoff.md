# Retry Queue: Exponential Backoff with Dead Letter

> Part of the [darkbot-templates](https://github.com/AMEOBIUS-space/darkbot-ai-templates) series — zero-dependency production templates.

Network calls fail. APIs rate-limit. Databases momentarily drop. The answer isn't to retry immediately (that makes it worse) — it's to back off exponentially and eventually give up gracefully.

## Usage

```python
from darkbot_templates.templates.retry_queue import RetryQueue, RetryItem

rq = RetryQueue()

def fetch_api(endpoint):
    return http_client.get(endpoint)

# Enqueue with retry config
item = RetryItem(
    func=fetch_api,
    args=("/users/42",),
    max_attempts=5,
    backoff_base=1.0,   # first retry after ~1s
    backoff_max=60.0,    # cap at 60s
)

rq.enqueue(item)

# Process the queue
rq.process_ready()  # runs items whose backoff has elapsed

# Check results
print(rq.stats)
# {"processed": 3, "succeeded": 2, "failed": 0, "dead_lettered": 1}
```

## Exponential Backoff + Jitter

```
Attempt 1: wait 1.0s + jitter (0-0.25s)
Attempt 2: wait 2.0s + jitter
Attempt 3: wait 4.0s + jitter
Attempt 4: wait 8.0s + jitter
Attempt 5: wait 16.0s + jitter
...
Capped at backoff_max (default 60s)
```

Jitter (25% random spread) prevents the **thundering herd** problem — if 100 clients all fail at once, they won't all retry at the exact same moment.

## Dead Letter Queue

After `max_attempts`, the item moves to the dead letter queue:

```python
for item in rq.dead_letter:
    print(f"FAILED: {item.name} after {item.attempts} attempts")
    print(f"  Last error: {item.last_error}")
    print(f"  Args: {item.args}")
```

Dead-lettered items can be inspected, manually retried, or sent to an alert system.

## Combining with Circuit Breaker

```python
from darkbot_templates.templates.retry_queue import RetryQueue, RetryItem
from darkbot_templates.templates.circuit_breaker import CircuitBreaker

cb = CircuitBreaker(failure_threshold=5, recovery_timeout=60.0)
rq = RetryQueue()

def resilient_call(endpoint):
    if not cb.allow():
        # Circuit open — queue for later instead of failing
        rq.enqueue(RetryItem(
            func=resilient_call,
            args=(endpoint,),
            max_attempts=3,
        ))
        return None

    try:
        result = http_client.get(endpoint)
        cb.success()
        return result
    except Exception as e:
        cb.failure()
        rq.enqueue(RetryItem(
            func=resilient_call,
            args=(endpoint,),
            max_attempts=3,
        ))
        return None
```

Circuit breaker stops the bleeding now; retry queue handles recovery later.

## Priority Queue

Items with higher priority are processed first:

```python
rq.enqueue(RetryItem(func=critical_sync, priority=10))
rq.enqueue(RetryItem(func=low_priority_sync, priority=1))
# critical_sync retries before low_priority_sync
```

## Testing

```bash
pytest tests/test_retry_queue.py -v
```

## References

- [AWS Exponential Backoff](https://docs.aws.amazon.com/general/latest/gr/api-retries.html)
- [Google SRE — Handling Overload](https://sre.google/sre-book/handling-overload/)

---

*darkbot-templates v1.8.5 — 30 templates, zero dependencies, 448 tests.*
