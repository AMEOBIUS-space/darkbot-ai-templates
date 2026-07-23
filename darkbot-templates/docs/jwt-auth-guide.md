# JWT Auth: Tokens Without PyJWT

> Part of the [darkbot-templates](https://github.com/AMEOBIUS-space/darkbot-ai-templates) series — zero-dependency production templates.

Every API needs authentication. PyJWT is the standard, but it pulls in cryptography dependencies. This template implements JWT with HMAC-SHA256/384/512 using only `hmac`, `hashlib`, `json`, and `base64` from the stdlib.

## Usage

```python
from darkbot_templates.templates.jwt_auth import JWTAuth

auth = JWTAuth(secret="your-secret-key", algorithm="HS256", default_expiry=3600)

# Generate token
token = auth.encode({"user_id": 42, "role": "admin"})
# → "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjo0Mi..."

# Verify and decode
payload = auth.decode(token)
print(payload["user_id"])  # 42
print(payload["role"])     # admin
print(payload["exp"])      # expiration timestamp
```

## Algorithms

| Algorithm | Hash | Use When |
|-----------|------|----------|
| HS256 | SHA-256 | Default — good balance of speed and security |
| HS384 | SHA-384 | Higher security requirements |
| HS512 | SHA-512 | Maximum HMAC security |

```python
auth = JWTAuth(secret="key", algorithm="HS512")
```

## Custom Expiry

```python
# 5-minute token for password reset
token = auth.encode({"action": "reset", "user_id": 42}, expiry=300)

# 7-day token for "remember me"
token = auth.encode({"user_id": 42}, expiry=604800)

# Refresh token
refresh = auth.create_refresh_token("user_42", expiry=2592000)  # 30 days
```

## Token Refresh

```python
# Old token expired? Refresh it:
try:
    payload = auth.decode(token)
except ValueError as e:
    if "expired" in str(e):
        new_token = auth.refresh(token)  # re-signs with fresh expiry
```

## Role-Based Access

```python
auth = JWTAuth(secret="key")

def require_role(token, role):
    payload = auth.decode(token)
    if payload.get("role") != role:
        raise PermissionError(f"Requires role: {role}")
    return payload

# Middleware pattern
def protected_endpoint(token):
    user = require_role(token, "admin")
    return {"message": f"Welcome, admin {user['user_id']}"}
```

## API Middleware Pattern

```python
from darkbot_templates.templates.jwt_auth import JWTAuth
from darkbot_templates.templates.http_client import HTTPClient

auth = JWTAuth(secret=os.environ["JWT_SECRET"])

def authenticate_request(headers):
    auth_header = headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        return None
    token = auth_header[7:]
    try:
        return auth.decode(token)
    except ValueError:
        return None

# In your request handler:
user = authenticate_request(request.headers)
if not user:
    return {"error": "unauthorized"}, 401
```

## Freelance Platform Auth

```python
auth = JWTAuth(secret=os.environ["API_SECRET"], default_expiry=86400)

# Login
def login(username, password):
    user = db.query_one("SELECT * FROM users WHERE username=?", (username,))
    if user and verify_password(password, user["password_hash"]):
        return auth.encode({"user_id": user["id"], "role": user["role"]})
    raise ValueError("Invalid credentials")

# Protect API endpoints
def get_bids(token):
    user = auth.decode(token)
    return db.query("SELECT * FROM bids WHERE user_id=?", (user["user_id"],))
```

## Security Notes

- **Secret length**: Use at least 32 random bytes (`os.urandom(32).hex()`)
- **Algorithm**: HS256 is fine for most use cases. Use HS512 for high-security
- **Expiry**: Always set short expiry for access tokens (15-60 min), longer for refresh
- **HTTPS only**: Never send tokens over plain HTTP
- **Not for passwords**: JWT is for session tokens, not password storage

## Testing

```bash
pytest tests/test_templates.py -k jwt -v
```

## References

- [RFC 7519 — JSON Web Token](https://datatracker.ietf.org/doc/html/rfc7519)
- [JWT Best Practices](https://datatracker.ietf.org/doc/html/rfc8725)

---

*darkbot-templates v1.8.5 — 30 templates, zero dependencies, 448 tests.*
