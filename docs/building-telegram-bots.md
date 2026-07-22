# Building Production Telegram Bots with darkbot-templates

> Zero-dependency Python templates for rapid Telegram bot development.

## Why darkbot-templates?

Every Telegram bot needs the same building blocks: rate limiting,
proxy rotation, task queues, config loading, health checks. Instead of
copying from Stack Overflow, darkbot-templates ships 26+ tested templates
that work together with zero external dependencies (Python stdlib only).

## Template Highlights

| Template | Purpose | Lines |
|----------|---------|-------|
| `jwt_auth` | JWT token generation/verification | ~180 |
| `rate_limiter` | Token bucket / sliding window | ~150 |
| `proxy_rotation` | SOCKS/HTTP proxy pool with health checks | ~200 |
| `webhook_server` | Async HTTP server for Telegram webhooks | ~220 |
| `task_queue` | Priority queue with retry logic | ~170 |
| `crypto_wallet` | Multi-chain wallet monitoring | ~190 |
| `cron_scheduler` | Lightweight cron-like job scheduler | ~160 |

## Quick Start

```python
from darkbot_templates import RateLimiter, ProxyRotation

limiter = RateLimiter(rate=30, per=60)  # 30 requests per minute
proxies = ProxyRotation(pool=["socks5://127.0.0.1:1080"])

if limiter.allow():
    response = proxies.get("https://api.telegram.org/bot.../sendMessage")
```

## Testing

All templates include unit tests (421 tests total):

```bash
pip install darkbot-templates
python -m pytest --no-cov
```

## Related

- [darkbot-templates on PyPI](https://pypi.org/project/darkbot-templates/)
- [Freelance portfolio](https://ameobius-space.github.io/kwork-portfolio/)
- [LaborX gig](https://laborx.com/gigs/python-automation-telegram-bots-cdp-api-integrations-105867)
