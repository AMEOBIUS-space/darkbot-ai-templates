# DarkBot AI Templates

> 30 production-ready Python templates: JWT, proxy rotation, rate limiter, webhook, task queue, Docker health, crypto wallet, cron, HTTP client, SQLite ORM, circuit breaker, backpressure, encryption, and more. Zero dependencies.

[![Python](https://img.shields.io/badge/python-3.10%2B-blue)](https://python.org)
[![Dependencies](https://img.shields.io/badge/dependencies-zero-success)](#)
[![License](https://img.shields.io/badge/license-MIT-blue)](LICENSE)

## What's New in 1.8.5

- **30 templates** total — added circuit_breaker, backpressure_handler, encrypt_decrypt, health_checker, service_registry
- **448 tests** — full coverage across all templates
- **Zero dependencies** — pure Python stdlib only

## Available Templates

| # | Template | Description |
|---|----------|-------------|
| 1 | jwt_auth | JWT generation/verification with HMAC-SHA256/384/512 |
| 2 | proxy_rotation | Proxy pool with health checks, 4 rotation strategies |
| 3 | rate_limiter | Token bucket + sliding window rate limiting |
| 4 | webhook_server | Async webhook receiver with signature verification |
| 5 | task_queue | Priority task queue with worker pool |
| 6 | config_loader | YAML/JSON/ENV config with validation |
| 7 | docker_health_check | Container health probe with HTTP/TCP/exec checks |
| 8 | crypto_wallet | HD wallet address generation + signing |
| 9 | email_sender | SMTP with templates, attachments, retry |
| 10 | cron_scheduler | Cron expression parser + job runner |
| 11 | http_client | Connection-pooled HTTP with retry + circuit breaker |
| 12 | sqlite_orm | Lightweight ORM over sqlite3 |
| 13 | log_analyzer | Parse + aggregate log files by level/pattern |
| 14 | csv_processor | Streaming CSV reader/writer with transforms |
| 15 | metrics_collector | Counter/histogram/timer → JSON export |
| 16 | cache_manager | TTL + LRU cache with invalidation |
| 17 | pubsub_broker | In-process pub/sub with topic filtering |
| 18 | state_machine | FSM with guards, actions, transitions |
| 19 | file_watcher | FileSystem watcher with debounce |
| 20 | retry_queue | Exponential backoff retry with dead-letter |
| 21 | signal_handler | Graceful shutdown via SIGTERM/SIGINT |
| 22 | plugin_loader | Discover + load entry-point plugins |
| 23 | connection_pool | Generic async connection pool |
| 24 | jsonrpc_server | JSON-RPC 2.0 server with method dispatch |
| 25 | cli_parser | Zero-dep argument parser with subcommands |
| 26 | encrypt_decrypt | AES-like encryption helper (stdlib) |
| 27 | circuit_breaker | Fail-fast circuit breaker with half-open recovery |
| 28 | backpressure_handler | Pressure-valve for bursty producers |
| 29 | health_checker | Composite health endpoint (DB/cache/API) |
| 30 | service_registry | In-memory service registry + discovery |

## Quick Start

```bash
pip install darkbot-templates
```

### JWT Authentication

```python
from darkbot_templates.templates.jwt_auth import JWTAuth

auth = JWTAuth(secret="your-secret-key")

# Generate token
token = auth.encode({"user_id": 42, "role": "admin"})
# eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...

# Verify and decode
payload = auth.decode(token)
print(payload["user_id"])  # 42
print(payload["role"])     # admin

# Refresh expired token
new_token = auth.refresh(token)

# Create 7-day refresh token
refresh = auth.create_refresh_token("user_42")
```

### Proxy Rotation

```python
from darkbot_templates.templates.proxy_rotation import ProxyRotationManager

manager = ProxyRotationManager(
    proxies=["http://proxy1:8080", "http://proxy2:8080", "http://proxy3:3128"],
    strategy="round_robin",  # or: random, least_failed, fastest
    max_failures=3,
    timeout=10,
)

# Get next proxy
proxy = manager.get_proxy()

# Fetch with automatic failover
content = manager.fetch("https://httpbin.org/ip")

# Check pool health
stats = manager.stats()
print(f"{stats['healthy']}/{stats['total_proxies']} healthy")
```

### Template Registry

```python
from darkbot_templates.registry import list_templates, get_template, manifest

# List all templates
for t in list_templates():
    print(f"  {t['name']}: {t['description']}")

# Get template source code
source = get_template("jwt_auth")

# Full manifest
m = manifest()
print(f"Version {m['version']}, {m['template_count']} templates")
```

## License

MIT

Freelance portfolio: [https://ameobius-space.github.io/kwork-portfolio/](https://ameobius-space.github.io/kwork-portfolio/)

Hire on LaborX: [https://laborx.com/gigs/python-automation-telegram-bots-cdp-api-integrations-105867](https://laborx.com/gigs/python-automation-telegram-bots-cdp-api-integrations-105867)

## Real-World Use Cases

- **LaborX automation**: 270+ job applications via JWT API + SOCKS proxy
- **Kwork monitoring**: Real-time dialog tracking across 6+ active clients
- **Telegram bot deployment**: aiogram 3.x bots with rate limiting + proxy rotation
- **CDP automation**: Chrome DevTools Protocol scraping with network interception
- **Freelance pipeline**: End-to-end bid/apply/track system with portfolio

## Articles

- [Building Production Telegram Bots](https://github.com/AMEOBIUS-space/darkbot-ai-templates/blob/main/docs/building-telegram-bots.md)
- [Circuit Breaker Resilience](docs/circuit-breaker-resilience.md)
- [Backpressure Load Shedding](docs/backpressure-load-shedding.md)
- [Health Checker Probe](docs/health-checker-probe.md)
- [SimpleCipher Obfuscation](docs/simple-cipher-obfuscation.md)
- [Service Registry Discovery](docs/service-registry-discovery.md)
- [State Machine FSM](docs/state-machine-fsm.md)
- [Connection Pool Reuse](docs/connection-pool-reuse.md)
- [Pub/Sub Event Bus](docs/pubsub-event-bus.md)
- [Retry Queue Backoff](docs/retry-queue-backoff.md)
- [Rate Limiter Patterns](docs/rate-limiter-patterns.md)
- [Cache Manager TTL+LRU](docs/cache-manager-ttl-lru.md)
- [JSON-RPC Server Guide](docs/jsonrpc-server-guide.md)
