# Backpressure: Shedding Load Before Your Queue Explodes

> Part of the [darkbot-templates](https://github.com/AMEOBIUS-space/darkbot-ai-templates) series — zero-dependency production templates.

When a producer outruns its consumer, you have two options: let the queue grow unbounded (OOM crash), or shed load deliberately. **Backpressure** is the valve that prevents the flood.

## The Problem

```
Producer ──1000 req/s──▶ Queue ──200 req/s──▶ Consumer
                                    │
                              grows by 800/s
                              → memory exhaustion
                              → consumer stalls
                              → cascading failure
```

Naive retry logic makes this worse — retrying failed items adds MORE pressure. The fix: measure queue depth, and when it crosses a threshold, stop accepting.

## Usage

```python
from darkbot_templates.templates.backpressure_handler import BackpressureHandler

bp = BackpressureHandler(max_depth=1000, shed_ratio=0.8)

def handle_request(request):
    if not bp.should_accept():
        bp.shed()
        return {"status": "shed", "retry_after": 30}

    bp.accept()
    try:
        result = process(request)
        return result
    finally:
        bp.complete()
```

- `max_depth=1000` — hard capacity
- `shed_ratio=0.8` — start shedding at 80% (800 items in flight)
- `should_accept()` — check before you accept
- `accept()` / `complete()` — bracket your work
- `shed()` — record the rejection (for metrics)

## Monitoring

```python
stats = bp.stats
# {
#   "depth": 642,
#   "max_depth": 1000,
#   "shed_threshold": 800,
#   "accepted": 15420,
#   "shed": 183,
#   "shed_ratio": 0.012
# }
```

A healthy system shows `shed_ratio < 0.01`. If it climbs above 0.05, either spin up more consumers or throttle the producer.

## Circuit Breaker vs Backpressure

| Pattern | What it protects | Signal | Action |
|---------|-----------------|--------|--------|
| Circuit Breaker | Downstream health | Failure count | Stop calling downstream |
| Backpressure | Your queue depth | In-flight items | Stop accepting new work |

Use **both**: circuit breaker prevents you from hammering a sick service; backpressure prevents your queue from drowning when you're the bottleneck.

```python
cb = CircuitBreaker(failure_threshold=5, recovery_timeout=30.0)
bp = BackpressureHandler(max_depth=500, shed_ratio=0.8)

def call_downstream(request):
    if not bp.should_accept():
        bp.shed()
        return None

    if not cb.allow():
        bp.shed()  # downstream is sick — don't even queue
        return None

    bp.accept()
    try:
        result = http_client.post(request)
        cb.success()
        return result
    except Exception:
        cb.failure()
        return None
    finally:
        bp.complete()
```

## Thread Safety

All methods acquire a `threading.Lock`. One `BackpressureHandler` instance is safe to share across worker threads.

## Testing

```bash
pytest tests/test_new_resilience.py -k backpressure -v
```

## References

- [Reactive Streams — Backpressure](https://www.reactive-streams.org/)
- [Kafka Consumer Lag](https://kafka.apache.org/documentation/#consumer_lag) — real-world backpressure metric
- [Little's Law](https://en.wikipedia.org/wiki/Little%27s_Law) — L = λW, the math behind queue depth

---

*darkbot-templates v1.8.5 — 30 templates, zero dependencies, 448 tests.*
