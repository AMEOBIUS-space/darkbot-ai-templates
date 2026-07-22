# Health Check Monitor

> HTTP endpoint monitoring with circuit breaker and alerting

## Features

- HTTP health checks (GET/POST, status code + body validation)
- Circuit breaker (closed → open → half-open → closed)
- Configurable failure threshold + recovery timeout
- Alert handlers (custom callbacks)
- Service status: healthy, degraded, unhealthy, unknown
- Overall system status aggregation
- Response time tracking
- History with configurable limit
- Statistics dashboard

## Quick Start

```python
from health import HealthMonitor

mon = HealthMonitor()
mon.add_check("api", "https://api.example.com/health", timeout=10)
mon.add_alert_handler(lambda a: send_slack(a))
mon.check_all()
print(mon.overall_status())
```

## Tests

```bash
python -m pytest tests/ -v
```

## License

MIT

Freelance portfolio: [https://ameobius-space.github.io/kwork-portfolio/](https://ameobius-space.github.io/kwork-portfolio/)
