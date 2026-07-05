# API Rate Limiter Middleware

> Token bucket + sliding window rate limiting for FastAPI, Flask, and Django

## Features

- **TokenBucket** — burst-capable with refill rate
- **SlidingWindow** — fixed count per time window
- Per-IP, per-user, per-API-key limits
- Custom limits per key (premium users)
- X-RateLimit headers (Limit, Remaining, Reset)
- 429 response with retry_after
- FastAPI/Starlette middleware + Flask before_request
- Per-key isolation

## Quick Start

```python
from rate_limiter import RateLimiterMiddleware

rl = RateLimiterMiddleware(default_limit=100, refill_rate=1.0)
rl.set_limit("premium_key", 1000)

allowed, retry_after, headers = rl.check("user_ip")
if not allowed:
    return 429, {"error": "rate_limited"}
```

## FastAPI Integration

```python
rl = RateLimiterMiddleware()
app.add_middleware(rl.fastapi_middleware())
```

## Tests

```bash
python -m pytest tests/ -v
```

## License

MIT
