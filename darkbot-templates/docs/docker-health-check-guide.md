# Docker Health Check: Container-Native Health Endpoints

> Part of the [darkbot-templates](https://github.com/AMEOBIUS-space/darkbot-ai-templates) series — zero-dependency production templates.

Docker's `HEALTHCHECK` directive polls an endpoint to decide if a container is healthy. This template provides both the server (runs inside your app) and the checker (what Docker calls).

## Usage

```python
from darkbot_templates.templates.docker_health_check import HealthCheckServer

# Run inside your containerized app
hc = HealthCheckServer(port=8080, path="/health")

# Register custom checks
hc.add_check("database", lambda: db.ping())
hc.add_check("cache", lambda: redis.ping())

# Mark as ready after startup
hc.set_healthy()
hc.start()  # listens on :8080/health

# Dockerfile: HEALTHCHECK CMD curl -f http://localhost:8080/health || exit 1
```

## Health States

| State | HTTP Response | When |
|-------|--------------|------|
| starting | 503 | App is initializing |
| healthy | 200 | All registered checks pass |
| unhealthy | 503 | One or more checks fail |

## Custom Check Functions

```python
hc = HealthCheckServer(port=8080)

def check_db():
    try:
        db.execute("SELECT 1")
        return True
    except:
        return False

def check_disk_space():
    usage = shutil.disk_usage("/")
    return usage.free > 1_000_000_000  # 1GB free

hc.add_check("database", check_db)
hc.add_check("disk", check_disk_space)

# Each check is called on every /health request
# If any returns False → state becomes unhealthy
```

## Dockerfile Integration

```dockerfile
FROM python:3.12-slim
COPY app.py .
HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
  CMD python -c "from darkbot_templates.templates.docker_health_check import check_endpoint; check_endpoint('http://localhost:8080/health')" || exit 1
CMD ["python", "app.py"]
```

## Response Format

```json
// GET /health → 200 OK
{
  "status": "healthy",
  "checks": {
    "database": {"healthy": true, "latency_ms": 2.1},
    "cache": {"healthy": true, "latency_ms": 0.3}
  },
  "uptime_seconds": 3600
}

// GET /health → 503 Service Unavailable
{
  "status": "unhealthy",
  "checks": {
    "database": {"healthy": false, "error": "ConnectionRefusedError"},
    "cache": {"healthy": true, "latency_ms": 0.3}
  }
}
```

## TCP Health Check (No HTTP)

```python
from darkbot_templates.templates.docker_health_check import TCPHealthCheck

# Simple TCP probe — is the port open?
checker = TCPHealthCheck(host="db.internal", port=5432, timeout=3.0)

if checker.check():
    print("Database port is open")
```

## Freelance Bot Health

```python
hc = HealthCheckServer(port=9090)

# Check all platform connections
hc.add_check("kwork_api", lambda: test_kwork_connection())
hc.add_check("laborx_api", lambda: test_laborx_connection())
hc.add_check("telegram", lambda: test_telegram_bot())
hc.add_check("database", lambda: db.ping())

hc.set_healthy()
hc.start()
```

## Testing

```bash
pytest tests/test_templates.py -k health -v
```

## References

- [Docker HEALTHCHECK](https://docs.docker.com/engine/reference/builder/#healthcheck)
- [Kubernetes Liveness Probes](https://kubernetes.io/docs/tasks/configure-pod-container/configure-liveness-readiness-startup-probes/)

---

*darkbot-templates v1.8.5 — 30 templates, zero dependencies, 448 tests.*
