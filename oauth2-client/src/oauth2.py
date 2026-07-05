"""OAuth2 Client — authorization code, client credentials, refresh, and PKCE."""
import base64
import hashlib
import json
import secrets
import time
import urllib.request
import urllib.parse
from typing import Dict, List, Optional, Tuple, Callable
from dataclasses import dataclass, asdict, field
from datetime import datetime


@dataclass
class TokenResponse:
    access_token: str
    token_type: str = "Bearer"
    expires_in: int = 3600
    refresh_token: str = ""
    scope: str = ""
    expires_at: float = 0.0
    raw: Dict = field(default_factory=dict)

    def __post_init__(self):
        if self.expires_at == 0.0 and self.expires_in > 0:
            self.expires_at = time.time() + self.expires_in

    @property
    def is_expired(self) -> bool:
        if not self.expires_at:
            return False
        return time.time() >= self.expires_at - 60  # 60s buffer

    @property
    def authorization_header(self) -> Dict:
        return {"Authorization": f"{self.token_type} {self.access_token}"}


class PKCE:
    """PKCE (Proof Key for Code Exchange) helpers."""

    @staticmethod
    def generate_verifier(length: int = 64) -> str:
        """Generate a code verifier."""
        return secrets.token_urlsafe(length)[:length]

    @staticmethod
    def generate_challenge(verifier: str, method: str = "S256") -> str:
        """Generate a code challenge from a verifier."""
        if method == "plain":
            return verifier
        elif method == "S256":
            digest = hashlib.sha256(verifier.encode()).digest()
            return base64.urlsafe_b64encode(digest).decode().rstrip("=")
        raise ValueError(f"Unsupported method: {method}")

    @staticmethod
    def create_pair(method: str = "S256") -> Tuple[str, str]:
        """Create (verifier, challenge) pair."""
        verifier = PKCE.generate_verifier()
        challenge = PKCE.generate_challenge(verifier, method)
        return verifier, challenge


class OAuth2Client:
    """OAuth2 client supporting multiple grant types."""

    def __init__(self, client_id: str, client_secret: str = "",
                 redirect_uri: str = "", token_url: str = "",
                 auth_url: str = "", scope: str = ""):
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri
        self.token_url = token_url
        self.auth_url = auth_url
        self.scope = scope
        self._token: Optional[TokenResponse] = None
        self._refresh_callback: Optional[Callable] = None

    def set_refresh_callback(self, callback: Callable):
        """Set callback called when token is refreshed."""
        self._refresh_callback = callback

    def get_authorization_url(self, state: str = None, scope: str = None,
                              pkce: Tuple[str, str] = None,
                              extra_params: Dict = None) -> str:
        """Build authorization URL for the authorization code flow."""
        params = {
            "response_type": "code",
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
        }
        if scope or self.scope:
            params["scope"] = scope or self.scope
        if state:
            params["state"] = state
        if pkce:
            params["code_challenge"] = pkce[1]
            params["code_challenge_method"] = "S256"
        if extra_params:
            params.update(extra_params)
        return f"{self.auth_url}?{urllib.parse.urlencode(params)}"

    def exchange_code(self, code: str, pkce_verifier: str = None) -> TokenResponse:
        """Exchange authorization code for tokens."""
        data = {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": self.redirect_uri,
            "client_id": self.client_id,
        }
        if self.client_secret:
            data["client_secret"] = self.client_secret
        if pkce_verifier:
            data["code_verifier"] = pkce_verifier
        return self._request_token(data)

    def client_credentials(self, scope: str = None) -> TokenResponse:
        """Get token via client credentials grant."""
        data = {
            "grant_type": "client_credentials",
            "client_id": self.client_id,
        }
        if self.client_secret:
            data["client_secret"] = self.client_secret
        if scope or self.scope:
            data["scope"] = scope or self.scope
        return self._request_token(data)

    def refresh_token(self, refresh_token: str = None) -> TokenResponse:
        """Refresh an access token."""
        token = refresh_token or (self._token.refresh_token if self._token else None)
        if not token:
            raise ValueError("No refresh token available")
        data = {
            "grant_type": "refresh_token",
            "refresh_token": token,
            "client_id": self.client_id,
        }
        if self.client_secret:
            data["client_secret"] = self.client_secret
        result = self._request_token(data)
        if self._refresh_callback:
            self._refresh_callback(result)
        return result

    def _request_token(self, data: Dict) -> TokenResponse:
        """Make token request to the token endpoint."""
        encoded_data = urllib.parse.urlencode(data).encode()
        req = urllib.request.Request(self.token_url, data=encoded_data, method="POST",
                                     headers={"Content-Type": "application/x-www-form-urlencoded"})
        resp = urllib.request.urlopen(req, timeout=30)
        raw = json.loads(resp.read().decode())
        token = TokenResponse(
            access_token=raw.get("access_token", ""),
            token_type=raw.get("token_type", "Bearer"),
            expires_in=raw.get("expires_in", 3600),
            refresh_token=raw.get("refresh_token", ""),
            scope=raw.get("scope", ""),
            raw=raw,
        )
        self._token = token
        return token

    def get_token(self) -> Optional[TokenResponse]:
        """Get current token, refreshing if expired."""
        if not self._token:
            return None
        if self._token.is_expired and self._token.refresh_token:
            return self.refresh_token()
        return self._token

    def set_token(self, token: TokenResponse):
        """Set a token directly (e.g., from storage)."""
        self._token = token

    @property
    def is_authenticated(self) -> bool:
        token = self.get_token()
        return token is not None and not token.is_expired

    def auth_headers(self) -> Dict:
        """Get authorization headers for API requests."""
        token = self.get_token()
        if not token:
            return {}
        return token.authorization_header

    def revoke(self, token: str, token_type_hint: str = "access_token",
               revoke_url: str = "") -> bool:
        """Revoke a token."""
        url = revoke_url or self.token_url.replace("/token", "/revoke")
        data = urllib.parse.urlencode({
            "token": token,
            "token_type_hint": token_type_hint,
            "client_id": self.client_id,
        }).encode()
        req = urllib.request.Request(url, data=data, method="POST",
                                     headers={"Content-Type": "application/x-www-form-urlencoded"})
        try:
            urllib.request.urlopen(req, timeout=10)
            return True
        except Exception:
            return False
