# Proxy Rotation: Health-Checked Pool Without requests

> Part of the [darkbot-templates](https://github.com/AMEOBIUS-space/darkbot-ai-templates) series — zero-dependency production templates.

Scraping at scale? API calls from a single IP will get rate-limited or blocked. A proxy rotation manager cycles through a pool of proxies, health-checks them, and fails over automatically.

## Rotation Strategies

| Strategy | How It Picks | Best For |
|----------|-------------|----------|
| round_robin | Cycle sequentially | Even load distribution |
| random | Random pick | Avoiding patterns |
| least_failed | Fewest failures | Reliability |
| fastest | Lowest latency | Speed-critical |

## Usage

```python
from darkbot_templates.templates.proxy_rotation import ProxyRotationManager

manager = ProxyRotationManager(
    proxies=[
        "http://proxy1.example.com:8080",
        "http://proxy2.example.com:3128",
        "http://user:pass@proxy3.example.com:8080",
    ],
    strategy="round_robin",
    max_failures=3,
    timeout=10,
)

# Get next proxy
proxy = manager.get_proxy()
# → "http://proxy1.example.com:8080"

# Fetch with automatic failover
content = manager.fetch("https://httpbin.org/ip")
# If proxy1 fails → tries proxy2 → tries proxy3

# Check pool health
stats = manager.stats()
print(f"{stats['healthy']}/{stats['total']} healthy")
```

## Health Checking

```python
manager = ProxyRotationManager(
    proxies=proxy_list,
    health_check_url="http://httpbin.org/ip",
    health_check_interval=300,  # re-check every 5 minutes
    max_failures=3,              # mark unhealthy after 3 failures
)

# Manual health check
manager.check_all()

# Get health report
for proxy_url, info in manager.proxies.items():
    status = "✓" if info["healthy"] else "✗"
    print(f"  {status} {proxy_url} — {info['latency_ms']}ms, {info['failures']} fails")
```

## Fetch with Failover

```python
# fetch() automatically tries the next proxy if the current one fails
try:
    response = manager.fetch("https://api.example.com/data")
    print(response)
except Exception as e:
    print(f"All proxies failed: {e}")
```

## Freelance Platform Scraping

```python
from darkbot_templates.templates.proxy_rotation import ProxyRotationManager
from darkbot_templates.templates.rate_limiter import TokenBucketRateLimiter

proxies = load_proxy_list("proxies.txt")  # one per line
manager = ProxyRotationManager(
    proxies=proxies,
    strategy="least_failed",
    max_failures=5,
    timeout=15,
)

limiter = TokenBucketRateLimiter(rate=2.0, capacity=5)  # 2 req/s

def scrape_kwork_jobs():
    while not limiter.allow("kwork"):
        time.sleep(limiter.wait_time("kwork"))

    proxy = manager.get_proxy()
    if not proxy:
        raise Exception("No healthy proxies")

    return manager.fetch("https://kwork.ru/projects?c=41")
```

## SOCKS5 Proxy Support

```python
# SOCKS proxies work with urllib via PySocks (optional, not bundled)
# HTTP/HTTPS proxies work out of the box

manager = ProxyRotationManager(
    proxies=[
        "http://http-proxy:8080",         # HTTP proxy
        "https://https-proxy:443",         # HTTPS proxy
        # "socks5://socks-proxy:1080",     # Requires PySocks
    ],
)
```

## Dynamic Proxy Addition

```python
# Add new proxies at runtime
manager.add_proxy("http://new-proxy:8080")

# Remove a bad proxy permanently
manager.remove_proxy("http://dead-proxy:8080")

# Get the fastest proxy
fastest = manager.get_fastest()
```

## Combining with Circuit Breaker

```python
from darkbot_templates.templates.circuit_breaker import CircuitBreaker

cb = CircuitBreaker(failure_threshold=10, recovery_timeout=60.0)

def resilient_fetch(url):
    if not cb.allow():
        return None  # circuit open — all proxies struggling

    proxy = manager.get_proxy()
    if not proxy:
        cb.failure()
        return None

    try:
        result = manager.fetch(url)
        cb.success()
        return result
    except Exception:
        cb.failure()
        return None
```

## Testing

```bash
pytest tests/test_templates.py -k proxy -v
```

## References

- [urllib ProxyHandler](https://docs.python.org/3/library/urllib.request.html#urllib.request.ProxyHandler)
- [Web Scraping Best Practices](https://blog.scrapinghub.com/web-scraping-best-practices)

---

*darkbot-templates v1.8.5 — 30 templates, zero dependencies, 448 tests.*
