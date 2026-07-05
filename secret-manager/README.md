# Secret Manager

> Encrypted secret storage with rotation tracking and .env integration

## Features

- Fernet symmetric encryption (AES-128-CBC + HMAC-SHA256)
- Master key-based encryption
- Version tracking (incremental)
- Rotation with expiry detection
- .env file import/export
- Tags and metadata
- History logging
- Thread-safe (RLock)
- Statistics

## Quick Start

```python
from secrets import SecretManager

mgr = SecretManager(master_key="your_master_key")
mgr.set_secret("api.stripe", "sk_live_xxx", rotation_days=90, tags=["production"])
print(mgr.get_secret("api.stripe"))
print(mgr.export_env())  # Export as .env format
```

## Tests

```bash
python -m pytest tests/ -v
```

## License

MIT
