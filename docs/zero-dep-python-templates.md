# Zero-Dependency Python Templates for Production

> How darkbot-templates ships 26+ production-ready modules with zero
> external packages — stdlib only.

## Why Zero Dependencies?

- No supply-chain risk (litellm, shai-hulud lessons)
- Instant install: `pip install darkbot-templates` is pure code
- Works offline, in restricted CI, on minimal Docker images
- Predictable behavior across Python 3.10–3.13

## Template Catalog

| Category | Templates |
|----------|-----------|
| Auth | `jwt_auth`, `signal_handler` |
| Networking | `http_client`, `proxy_rotation`, `connection_pool` |
| Queues | `task_queue`, `retry_queue`, `pubsub_broker` |
| Data | `sqlite_orm`, `csv_processor`, `cache_manager` |
| Ops | `cron_scheduler`, `docker_health_check`, `metrics_collector` |
| Bots | `webhook_server`, `rate_limiter`, `config_loader` |
| Crypto | `crypto_wallet`, `encrypt_decrypt` |

## Composition Pattern

Templates compose via plain imports:

```python
from darkbot_templates import RateLimiter, ProxyRotation, TaskQueue

limiter = RateLimiter(rate=30, per=60)
proxies = ProxyRotation(pool=["socks5://127.0.0.1:1080"])
q = TaskQueue(maxsize=1000)

if limiter.allow():
    q.put({"url": "https://api.telegram.org/...", "proxy": proxies.next()})
```

## Testing

421 unit tests, stdlib + pytest only:

```bash
pip install darkbot-templates
python -m pytest --no-cov
```

## Related

- [darkbot-templates on PyPI](https://pypi.org/project/darkbot-templates/)
- [Building Production Telegram Bots](building-telegram-bots.md)
- [Freelance portfolio](https://ameobius-space.github.io/kwork-portfolio/)
