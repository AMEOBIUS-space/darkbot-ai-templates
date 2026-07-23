# Rate Limiter: Token Bucket and Sliding Window

> Part of the [darkbot-templates](https://github.com/AMEOBIUS-space/darkbot-ai-templates) series — zero-dependency production templates.

Every API has limits. Whether you're calling OpenAI (60 RPM), GitHub (5000/hr), or your own database pool (100 concurrent), a rate limiter keeps you under the ceiling. This template ships two algorithms: **token bucket** (smooth with bursts) and **sliding window** (strict per-period).

## Token Bucket

Tokens accumulate at `rate` per second, up to `capacity` max. Each request consumes 1 token. If the bucket is empty, the request is denied.

```python
from darkbot_templates.templates.rate_limiter import TokenBucketRateLimiter

# 10 requests/second, burst up to 20
limiter = TokenBucketRateLimiter(rate=10.0, capacity=20)

if limiter.allow("user_42"):
    call_api()
else:
    retry_later()

# Check without consuming
print(limiter.peek("user_42"))  # → 7.3

# How long to wait for N tokens?
print(limiter.wait_time("user_42", tokens=5))  # → 0.3 seconds
```

**Good for:** API gateways, network shaping, scenarios where bursts are acceptable.

## Sliding Window

Strict N requests per time window. No bursts beyond the limit.

```python
from darkbot_templates.templates.rate_limiter import SlidingWindowRateLimiter

# 100 requests per 60 seconds
limiter = SlidingWindowRateLimiter(max_requests=100, window=60.0)

for i in range(105):
    if limiter.allow("api_key_xxx"):
        print(f"  Request {i}: allowed")
    else:
        print(f"  Request {i}: DENIED")
# Requests 0-99: allowed
# Requests 100-104: denied
```

**Good for:** Strict API quotas, billing-tier limits, per-user caps.

## Per-Key Limiting (Multi-Tenant)

Both limiters accept a `key` parameter — each key gets its own bucket/window:

```python
limiter = TokenBucketRateLimiter(rate=5.0, capacity=10)

# Each user gets independent limits
limiter.allow("user_1")  # user_1's bucket
limiter.allow("user_2")  # user_2's bucket
limiter.allow("user_1")  # user_1's bucket again
```

## API Gateway Pattern

```python
limiter = TokenBucketRateLimiter(rate=100.0, capacity=200)

def gateway(endpoint, api_key, payload):
    if not limiter.allow(api_key):
        return {"error": "rate_limited", "retry_after": limiter.wait_time(api_key)}

    return handle_request(endpoint, payload)
```

## Freelance Platform Rate Limiting

```python
limiter = SlidingWindowRateLimiter(max_requests=30, window=60.0)

def apply_to_job(job_id):
    if not limiter.allow("kwork"):
        print("Rate limited — waiting")
        time.sleep(limiter.wait_time("kwork"))
    submit_application(job_id)
```

## Testing

```bash
pytest tests/test_rate_limiter.py -v
```

## References

- [Stripe Rate Limiting](https://stripe.com/blog/rate-limiters)
- [Cloudflare Rate Limiting](https://developers.cloudflare.com/firewall/cf-firewall-rules/rate-limiting/)

---

*darkbot-templates v1.8.5 — 30 templates, zero dependencies, 448 tests.*
