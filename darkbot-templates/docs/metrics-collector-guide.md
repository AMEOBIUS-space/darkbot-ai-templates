# Metrics Collector: Prometheus-Style Metrics Without the Client

> Part of the [darkbot-templates](https://github.com/AMEOBIUS-space/darkbot-ai-templates) series — zero-dependency production templates.

You want metrics — counters, gauges, histograms — but you don't want to pull in the entire `prometheus_client` library. This template gives you the four core metric types in pure stdlib, with JSON export.

## Metric Types

| Type | What It Tracks | Example |
|------|---------------|---------|
| Counter | Monotonically increasing value | Total requests served |
| Gauge | Value that goes up and down | Active connections |
| Histogram | Distribution of values | Request latency percentiles |
| Timer | Duration measurement (histogram wrapper) | Database query time |

## Usage

```python
from darkbot_templates.templates.metrics_collector import MetricsCollector

metrics = MetricsCollector()

# Register metrics
requests = metrics.counter("http_requests_total", "Total HTTP requests", labels=["method", "status"])
active = metrics.gauge("active_connections", "Current connections")
latency = metrics.histogram("request_duration_seconds", "Request latency",
                            buckets=[0.01, 0.05, 0.1, 0.5, 1.0, 5.0])

# Use them
requests.inc(method="GET", status="200")
requests.inc(method="GET", status="200")
requests.inc(method="POST", status="500")

active.set(42)
active.inc()   # 43
active.dec()   # 42

latency.observe(0.023)
latency.observe(0.187)
latency.observe(0.051)
```

## Labeled Metrics

Counters and gauges support labels for dimensional data:

```python
requests = metrics.counter("api_calls", labels=["endpoint", "method"])

requests.inc(endpoint="/users", method="GET")
requests.inc(endpoint="/users", method="GET")
requests.inc(endpoint="/orders", method="POST")

print(requests.values())
# {"endpoint=/users|method=GET": 2, "endpoint=/orders|method=POST": 1}
```

## Histogram Percentiles

```python
latency = metrics.histogram("response_time", buckets=[0.01, 0.05, 0.1, 0.5, 1.0])

for ms in [0.01, 0.03, 0.08, 0.12, 0.45, 0.67, 0.89, 0.95]:
    latency.observe(ms)

stats = latency.stats()
print(stats)
# {
#   "count": 8,
#   "sum": 3.2,
#   "avg": 0.4,
#   "p50": 0.285,   # median
#   "p95": 0.89,
#   "p99": 0.95,
#   "buckets": {"0.01": 1, "0.05": 2, "0.1": 3, "0.5": 6, "1.0": 8}
# }
```

## Timer Context Manager

```python
db_query = metrics.timer("db_query_seconds")

with db_query:
    result = db.execute("SELECT * FROM users")
# Automatically records elapsed time as a histogram observation
```

## JSON Export

```python
export = metrics.export_json()
# {
#   "counters": {"http_requests_total": {...}},
#   "gauges": {"active_connections": 42},
#   "histograms": {"request_duration_seconds": {...}}
# }
```

Expose this via your health endpoint or a `/metrics` endpoint.

## Freelance Platform Monitoring

```python
metrics = MetricsCollector()

bids = metrics.counter("bids_submitted", labels=["platform"])
earnings = metrics.gauge("pending_earnings_usd")
response_time = metrics.histogram("platform_response_time")

def submit_bid(platform, amount):
    with response_time:
        result = api.submit(platform, amount)
    bids.inc(platform=platform)
    if result.success:
        earnings.inc(amount)
```

## Thread Safety

All metric types use `threading.Lock`. Safe to share across threads.

## Testing

```bash
pytest tests/test_metrics.py -v
```

## References

- [Prometheus Metric Types](https://prometheus.io/docs/concepts/metric_types/)
- [OpenMetrics Spec](https://openmetrics.io/)

---

*darkbot-templates v1.8.5 — 30 templates, zero dependencies, 448 tests.*
