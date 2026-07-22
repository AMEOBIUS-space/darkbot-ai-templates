# DarkBot AI Templates

> 20 production-ready Python code templates: TG bots, scrapers, AI agents, crypto trading, Tor, JWT auth, proxy rotation. Zero dependencies.

[![Python](https://img.shields.io/badge/python-3.10%2B-blue)](https://python.org)
[![Dependencies](https://img.shields.io/badge/dependencies-zero-success)](#)
[![License](https://img.shields.io/badge/license-MIT-blue)](LICENSE)

## What's New in 1.6.0

- **JWT Auth template** — HMAC-SHA256/384/512 token generation, verification, refresh tokens. Pure stdlib (hmac, hashlib, json, base64).
- **Proxy Rotation Manager** — round-robin, random, least-failed, fastest strategies with health checking and EMA latency tracking.
- **Template registry** — `list_templates()`, `get_template(name)`, `manifest()` for programmatic discovery.
- **Importable templates** — templates ship as Python modules, not just text files.

## Available Templates

| # | Template | Description |
|---|----------|-------------|
| 1 | jwt_auth | JWT token generation/verification with HMAC-SHA256/384/512 |
| 2 | proxy_rotation | Proxy pool with health checks, 4 rotation strategies, failover |
| 3-20 | (existing) | TG bots, scrapers, AI agents, crypto trading, Tor, and more |

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
