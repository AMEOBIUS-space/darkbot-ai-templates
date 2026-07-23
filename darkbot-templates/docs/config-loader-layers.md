# Config Loader: Layered Configuration Without Frameworks

> Part of the [darkbot-templates](https://github.com/AMEOBIUS-space/darkbot-ai-templates) series — zero-dependency production templates.

Every app needs config: database URLs, API keys, feature flags, timeouts. Hardcoding them leads to disaster. This template gives you layered loading — defaults, file, env vars, CLI overrides — with dot-path access.

## Layered Loading

```
defaults ← config.json ← environment variables ← runtime overrides
```

Each layer overrides the previous. Later layers win.

```python
from darkbot_templates.templates.config_loader import ConfigLoader

defaults = {
    "database": {"host": "localhost", "port": 5432, "pool_size": 10},
    "api": {"timeout": 30, "retries": 3},
    "debug": False,
}

config = ConfigLoader(defaults=defaults, env_prefix="APP")

# Load from file (overrides defaults)
config.load_file("config.json")

# Load from environment (overrides file)
# APP_DATABASE__HOST=db.prod.example.com → config.get("database.host")
config.load_env()

# Runtime override (overrides everything)
config.set("debug", True)

print(config.get("database.host"))  # → "db.prod.example.com" (from env)
print(config.get("debug"))           # → True (from override)
```

## Dot-Path Access

No more `config["database"]["host"]` — use dot paths:

```python
config.get("database.host")      # nested dict traversal
config.get("database.port", 5432) # with default fallback
config.get("api.timeout")
config.set("database.pool_size", 20)
```

## Environment Variable Mapping

Env vars map to config paths via `prefix + separator`:

```
APP_DATABASE__HOST → database.host
APP_API__TIMEOUT   → api.timeout
APP_DEBUG          → debug
```

```python
# Set in shell:
# export APP_DATABASE__HOST="prod-db.internal"
# export APP_API__TIMEOUT="60"

config = ConfigLoader(defaults=defaults, env_prefix="APP", env_separator="__")
config.load_env()
config.get("database.host")  # → "prod-db.internal"
config.get("api.timeout")    # → 60 (parsed as int automatically)
```

## Type Coercion

Env vars are always strings. ConfigLoader coerces common types:

```python
# APP_DEBUG="true" → True (boolean)
# APP_DATABASE__PORT="5432" → 5432 (int)
# APP_API__RATE="1.5" → 1.5 (float)
```

## Layer Tracking

Debug where each value came from:

```python
print(config.layers)
# ["defaults", "file:config.json", "env", "overrides"]
```

## 12-Factor App Pattern

```python
config = ConfigLoader(
    defaults={
        "port": 8000,
        "workers": 4,
        "database_url": "sqlite:///local.db",
    },
    env_prefix="APP",
)

config.load_file("/etc/myapp/config.json")  # system config
config.load_env()                            # 12-factor: env vars override

port = config.get("port")
db_url = config.get("database_url")
```

## Freelance Platform Config

```python
config = ConfigLoader(defaults={
    "kwork": {"base_url": "https://kwork.ru", "timeout": 30},
    "laborx": {"base_url": "https://laborx.com", "timeout": 30},
    "proxy": {"host": None, "port": 11080},
})

config.load_file("freelance_config.json")
config.load_env()

# Override for a specific run
config.set("kwork.timeout", 60)  # longer timeout for slow network
```

## Testing

```bash
pytest tests/test_config_loader.py -v
```

## References

- [12-Factor App Config](https://12factor.net/config)
- [Spring Boot Externalized Config](https://docs.spring.io/spring-boot/docs/current/reference/html/features.html#features.external-config)

---

*darkbot-templates v1.8.5 — 30 templates, zero dependencies, 448 tests.*
