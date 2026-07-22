# API Key Manager

> Secure API key generation, rotation, validation, and scope management

## Features

- Cryptographically secure key generation (secrets.token_hex)
- HMAC-SHA256 key hashing (never store raw keys)
- Scope-based authorization (read, write, admin)
- Key rotation (revoke old + create new with same scopes)
- Expiry management with cleanup
- Usage tracking (count, last_used)
- Rate limit per key
- Key revocation
- Statistics dashboard

## Quick Start

```python
from key_manager import APIKeyManager

mgr = APIKeyManager(master_secret="your_secret")
raw, key = mgr.create_key(scopes=["read", "write"], rate_limit=100)

# Validate
valid, key, msg = mgr.validate_key(raw)
if valid and mgr.check_scope(key, "write"):
    # Allow write operation
    pass
```

## Tests

```bash
python -m pytest tests/ -v
```

## License

MIT

Freelance portfolio: [https://ameobius-space.github.io/kwork-portfolio/](https://ameobius-space.github.io/kwork-portfolio/)
