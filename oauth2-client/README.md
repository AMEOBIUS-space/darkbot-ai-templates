# OAuth2 Client

> Authorization code, client credentials, refresh, and PKCE support

## Features

- Authorization code flow with PKCE (S256 + plain)
- Client credentials grant
- Token refresh with callback
- Token expiration detection (60s buffer)
- Authorization URL builder with state + PKCE + extra params
- Token revocation
- Auth header generation
- Token storage/retrieval

## Quick Start

```python
from oauth2 import OAuth2Client, PKCE

client = OAuth2Client(
    client_id="your_id",
    client_secret="your_secret",
    redirect_uri="https://app.com/callback",
    token_url="https://auth.example.com/token",
    auth_url="https://auth.example.com/authorize",
    scope="read write",
)

# Authorization code flow with PKCE
verifier, challenge = PKCE.create_pair()
auth_url = client.get_authorization_url(state="xyz", pkce=(verifier, challenge))
# Redirect user to auth_url, get code from callback
token = client.exchange_code(code, pkce_verifier=verifier)

# Client credentials flow
token = client.client_credentials()

# API calls
headers = client.auth_headers()  # {"Authorization": "Bearer ..."}
```

## Tests

```bash
python -m pytest tests/ -v
```

## License

MIT
