# SimpleCipher: Config Obfuscation Without Crypto Dependencies

> Part of the [darkbot-templates](https://github.com/AMEOBIUS-space/darkbot-ai-templates) series — zero-dependency production templates.

**This is obfuscation, not encryption.** Use it for config secrets, API tokens in dev fixtures, and anything where "unreadable without the key" is enough. Do NOT use it for passwords, financial data, or PII — use `cryptography` or PyNaCl for real security.

## What It Provides

- **Confusion** — ciphertext is unreadable without the key
- **Integrity** — HMAC tag detects tampering
- **Key stretching** — 10,000 SHA-256 iterations slow brute force
- **Salt + IV** — same plaintext produces different ciphertext each time

## What It Does NOT Provide

- Semantic security against known-plaintext attacks
- Resistance to chosen-ciphertext attacks
- Side-channel protection

## Usage

```python
from darkbot_templates.templates.encrypt_decrypt import SimpleCipher

cipher = SimpleCipher(key="my-secret-passphrase")

# Encrypt
token = cipher.encrypt("sk-live-abc123xyz")
# → base64 string: "aGVsbG8...=="

# Decrypt
plain = cipher.decrypt(token)
# → "sk-live-abc123xyz"
```

## Wire Format

```
base64( salt[16] + iv[16] + hmac_tag[32] + encrypted_data[...] )
```

1. Random salt → stretch key via iterative SHA-256
2. Random IV → XOR stream cipher
3. HMAC-SHA256 over ciphertext → integrity
4. Everything concatenated, base64-encoded

## Config Secrets Pattern

```python
import os
from darkbot_templates.templates.encrypt_decrypt import SimpleCipher

# At deploy time: encrypt once
cipher = SimpleCipher(key=os.environ["MASTER_KEY"])
encrypted_db_pass = cipher.encrypt(os.environ["DB_PASSWORD"])
# Store encrypted_db_pass in config.yaml

# At runtime: decrypt
cipher = SimpleCipher(key=os.environ["MASTER_KEY"])
db_pass = cipher.decrypt(config["db_password_encrypted"])
```

Only `MASTER_KEY` needs to live in the environment. Everything else can sit in config files as opaque base64.

## Integrity Check

```python
cipher = SimpleCipher(key="secret")
token = cipher.encrypt("sensitive-data")

# Tamper with the ciphertext
tampered = token[:-4] + "XXXX"

try:
    cipher.decrypt(tampered)
except ValueError as e:
    print(e)  # "HMAC verification failed — data may be tampered"
```

## When to Use vs Real Crypto

| Use Case | SimpleCipher | cryptography / PyNaCl |
|----------|-------------|----------------------|
| Dev/test fixtures | Yes | Overkill |
| Config obfuscation | Yes | Optional |
| API tokens in CI secrets | Yes | Better |
| User passwords | **NO** | bcrypt / argon2 |
| Financial data | **NO** | AES-GCM |
| End-to-end messaging | **NO** | libsodium |

## Testing

```bash
pytest tests/test_new_templates.py -k encrypt -v
```

## References

- [OWASP Cryptographic Storage Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Cryptographic_Storage_Cheat_Sheet.html)
- [NIST SP 800-132 — PBKDF](https://csrc.nist.gov/publications/detail/sp/800-132/final)

---

*darkbot-templates v1.8.5 — 30 templates, zero dependencies, 448 tests.*
