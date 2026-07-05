# Metrics Collector

> Counters, gauges, histograms, and timers with Prometheus export

## Features

- Counter (inc, reset)
- Gauge (set, inc, dec)
- Histogram (observe, percentile p50/p95/p99, avg)
- Timer (context manager + decorator)
- JSON export
- Prometheus text format export
- Thread-safe (locks)
- Idempotent metric registration

## Quick Start

```python
from metrics import MetricsCollector

m = MetricsCollector()
m.counter("requests").inc()
m.gauge("temperature").set(25.5)

timer = m.timer("db_query")
with timer:
    db.execute("SELECT 1")

print(m.export_prometheus())
```

## Tests

```bash
python -m pytest tests/ -v
```

## License

MIT
