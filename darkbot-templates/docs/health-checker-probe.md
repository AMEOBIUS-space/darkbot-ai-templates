# Health Checker: Probe Endpoints Without Dependencies

> Part of the [darkbot-templates](https://github.com/AMEOBIUS-space/darkbot-ai-templates) series — zero-dependency production templates.

Every production service needs a health endpoint. And every client needs to probe it. This template is a pure-stdlib HTTP health checker — no `requests`, no `httpx`, no asyncio.

## Usage

```python
from darkbot_templates.templates.health_checker import HealthChecker

hc = HealthChecker(timeout=5.0)

result = hc.check("https://api.example.com/health")
# {
#   "url": "https://api.example.com/health",
#   "status": "up",        # "up" | "degraded" | "down"
#   "latency_ms": 42.3,
#   "status_code": 200,
#   "error": None
# }
```

## Status Semantics

| Status | Meaning | When |
|--------|---------|------|
| `up` | Healthy | HTTP 2xx/3xx/4xx |
| `degraded` | Responding but sick | HTTP 5xx |
| `down` | Unreachable | timeout, DNS fail, connection refused |

4xx counts as `up` because the server is alive — it's just rejecting the request. 5xx means the server is struggling. Network errors mean it's gone.

## Tracking Uptime

```python
hc = HealthChecker(timeout=3.0)

for _ in range(10):
    hc.check("https://api.example.com/health")
    time.sleep(30)

print(f"Uptime: {hc.uptime_percentage}%")
# Uptime: 90.0%

for entry in hc.history:
    print(f"{entry['status']:8s} {entry['latency_ms']:6.1f}ms  {entry['url']}")
```

History is capped at 100 entries (rolling window). Call `hc.reset()` to clear.

## Composite Health (Multiple Services)

```python
services = {
    "api": "https://api.example.com/health",
    "db": "https://db.example.com/ping",
    "cache": "https://cache.example.com/status",
}

hc = HealthChecker(timeout=2.0)
report = {}
for name, url in services.items():
    report[name] = hc.check(url)

all_up = all(r["status"] == "up" for r in report.values())
print("OVERALL:", "healthy" if all_up else "unhealthy")
for name, r in report.items():
    print(f"  {name}: {r['status']} ({r['latency_ms']}ms)")
```

## Pairing with Circuit Breaker

```python
from darkbot_templates.templates.circuit_breaker import CircuitBreaker
from darkbot_templates.templates.health_checker import HealthChecker

cb = CircuitBreaker(failure_threshold=3, recovery_timeout=60.0)
hc = HealthChecker(timeout=2.0)

def probe_and_gate(url):
    if not cb.allow():
        return {"status": "circuit_open"}

    result = hc.check(url)
    if result["status"] == "up":
        cb.success()
    else:
        cb.failure()
    return result
```

Health checker measures. Circuit breaker decides. Together they form a basic self-healing probe loop.

## Testing

```bash
pytest tests/test_health_checker.py -v
```

## References

- [Kubernetes Liveness/Readiness Probes](https://kubernetes.io/docs/tasks/configure-pod-container/configure-liveness-readiness-startup-probes/)
- [RFC 9110 — HTTP Semantics](https://www.rfc-editor.org/rfc/rfc9110.html)

---

*darkbot-templates v1.8.5 — 30 templates, zero dependencies, 448 tests.*
