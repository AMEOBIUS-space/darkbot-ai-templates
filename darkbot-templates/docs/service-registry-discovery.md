# Service Registry: Client-Side Discovery Without Consul

> Part of the [darkbot-templates](https://github.com/AMEOBIUS-space/darkbot-ai-templates) series — zero-dependency production templates.

Before Kubernetes and Consul, service discovery was a dict and a round-robin pointer. Sometimes that's all you need — especially for small clusters, test harnesses, and sidecar-less setups.

## Usage

```python
from darkbot_templates.templates.service_registry import ServiceRegistry

reg = ServiceRegistry()

# Register instances
reg.register("api", "http://node1:8080")
reg.register("api", "http://node2:8080")
reg.register("api", "http://node3:8080")

# Round-robin selection
for _ in range(5):
    endpoint = reg.get("api")
    print(endpoint)
# http://node1:8080
# http://node2:8080
# http://node3:8080
# http://node1:8080
# http://node2:8080
```

## Deregister on Failure

```python
from darkbot_templates.templates.health_checker import HealthChecker

reg = ServiceRegistry()
hc = HealthChecker(timeout=2.0)

reg.register("api", "http://node1:8080")
reg.register("api", "http://node2:8080")

# Periodic health sweep
for endpoint in reg.list("api"):
    result = hc.check(f"{endpoint}/health")
    if result["status"] == "down":
        reg.deregister("api", endpoint)
        print(f"Removed unhealthy: {endpoint}")
```

## Full Stack: Registry + Circuit Breaker + Backpressure

```python
from darkbot_templates.templates.service_registry import ServiceRegistry
from darkbot_templates.templates.circuit_breaker import CircuitBreaker

reg = ServiceRegistry()
reg.register("payment", "http://pay-svc-1:8080")
reg.register("payment", "http://pay-svc-2:8080")

cb = CircuitBreaker(failure_threshold=5, recovery_timeout=30.0)

def call_payment(payload):
    if not cb.allow():
        return None  # circuit open

    endpoint = reg.get("payment")
    if not endpoint:
        cb.failure()
        return None  # no instances

    try:
        result = http_client.post(f"{endpoint}/charge", json=payload)
        cb.success()
        return result
    except Exception:
        cb.failure()
        # Optionally deregister after repeated failures
        return None
```

## Thread Safety

All methods acquire a `threading.Lock`. One registry shared across threads is safe. The internal `itertools.cycle` is rebuilt atomically on register/deregister.

## When to Use a Real Service Mesh

| Use This Template | Use Consul / etcd / k8s |
|---|---|
| < 20 service instances | > 20 instances |
| Single process or small cluster | Multi-node clusters |
| Test/staging harnesses | Production with failover |
| No network partition tolerance needed | Cross-AZ / cross-region |

## Testing

```bash
pytest tests/test_new_templates.py -k service_registry -v
```

## References

- [Service Discovery Pattern](https://microservices.io/patterns/service-registry.html)
- [Client-Side vs Server-Side Discovery](https://martinfowler.com/articles/microservice-testing/)

---

*darkbot-templates v1.8.5 — 30 templates, zero dependencies, 448 tests.*
