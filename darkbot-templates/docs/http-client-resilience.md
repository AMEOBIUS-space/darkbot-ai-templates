# HTTP Client: Retry, Backoff, and Circuit Breaker in One

> Part of the [darkbot-templates](https://github.com/AMEOBIUS-space/darkbot-ai-templates) series — zero-dependency production templates.

`requests` is great, but it doesn't retry, doesn't back off, and doesn't circuit-break. This template wraps `urllib.request` with production resilience patterns — zero dependencies.

## Usage

```python
from darkbot_templates.templates.http_client import HTTPClient

client = HTTPClient(
    base_url="https://api.example.com",
    timeout=10,
    max_retries=3,
    backoff_base=1.0,
    backoff_max=30.0,
    circuit_threshold=5,
    circuit_cooldown=60.0,
)

# GET
resp = client.get("/users/42")
# → {"status": 200, "body": {...}, "elapsed_ms": 45}

# POST
resp = client.post("/orders", json={"product": "widget", "qty": 3})

# PUT
resp = client.put("/users/42", json={"name": "Alice"})

# DELETE
resp = client.delete("/orders/99")
```

## Built-in Retry with Backoff

```python
client = HTTPClient(max_retries=5, backoff_base=2.0)

# If the request fails:
# Attempt 1 → fail → wait 2s
# Attempt 2 → fail → wait 4s
# Attempt 3 → fail → wait 8s
# Attempt 4 → fail → wait 16s
# Attempt 5 → fail → raise exception
```

Retries are automatic for:
- Connection errors (network down)
- Timeouts
- 429 Too Many Requests
- 502/503/504 server errors

Client errors (400/401/403/404/409) are **not** retried — retrying won't help.

## Circuit Breaker Integration

```python
client = HTTPClient(circuit_threshold=5, circuit_cooldown=60.0)

# After 5 consecutive failures, the circuit opens:
resp = client.get("/flaky-endpoint")
# → {"status": "circuit_open", "body": None}

# After 60 seconds, circuit goes half-open:
# One test request is allowed. If it succeeds → circuit closes.
```

## Response Object

```python
resp = client.get("/health")

print(resp.status_code)   # 200
print(resp.ok)            # True
print(resp.body)          # {"status": "healthy"} (auto-parsed JSON)
print(resp.elapsed_ms)    # 42.3
print(resp.headers)       # {"Content-Type": "application/json", ...}
print(resp.from_cache)    # False
print(resp.attempts)      # 1 (how many tries it took)
```

## Custom Headers and Auth

```python
client = HTTPClient(
    base_url="https://api.github.com",
    headers={"Authorization": "token ghp_xxx", "Accept": "application/vnd.github+json"},
)

repos = client.get("/user/repos", params={"per_page": 100})
```

## Query Parameters

```python
resp = client.get("/search", params={"q": "python", "sort": "stars", "page": 1})
# → GET /search?q=python&sort=stars&page=1
```

## Streaming Downloads

```python
for chunk in client.stream("/large-file.zip", chunk_size=8192):
    write_to_disk(chunk)
```

## Freelance Platform Client

```python
kwork = HTTPClient(
    base_url="https://kwork.ru/v1",
    timeout=30,
    max_retries=3,
    headers={"Authorization": f"Bearer {token}"},
)

# List projects
resp = kwork.get("/projects", params={"category": "python", "page": 1})

# Submit bid
resp = kwork.post("/bids", json={"project_id": 12345, "amount": 500})
```

## Thread Safety

Each `HTTPClient` instance maintains its own circuit breaker state. For shared circuit breaking across endpoints, use a separate `CircuitBreaker` instance.

## Testing

```bash
pytest tests/test_http_client.py -v
```

## References

- [urllib.request docs](https://docs.python.org/3/library/urllib.request.html)
- [HTTP Retry-After header](https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Retry-After)

---

*darkbot-templates v1.8.5 — 30 templates, zero dependencies, 448 tests.*
