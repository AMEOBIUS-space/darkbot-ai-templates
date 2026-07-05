"""API Key Manager — secure key generation, rotation, validation, and scope management."""
import hashlib
import hmac
import secrets
import time
import json
from typing import Dict, List, Optional, Set, Tuple
from dataclasses import dataclass, asdict, field
from datetime import datetime, timedelta


@dataclass
class APIKey:
    key_id: str
    key_hash: str  # Store hash, not raw key
    prefix: str  # First 8 chars for identification
    scopes: List[str]
    rate_limit: int  # requests per minute
    created_at: str
    expires_at: str
    last_used: str = ""
    active: bool = True
    description: str = ""
    usage_count: int = 0


class APIKeyManager:
    """Manage API keys with secure storage, rotation, and scope validation."""

    KEY_PREFIX = "dk_"  # DarkBot key prefix
    KEY_LENGTH = 32  # bytes of randomness
    DEFAULT_EXPIRY_DAYS = 90

    def __init__(self, master_secret: str = ""):
        self.master_secret = master_secret
        self.keys: Dict[str, APIKey] = {}  # key_id -> APIKey
        self._revoked: Set[str] = set()

    def _generate_key(self) -> Tuple[str, str, str]:
        """Generate (raw_key, key_id, key_hash)."""
        raw = self.KEY_PREFIX + secrets.token_hex(self.KEY_LENGTH)
        key_id = hashlib.sha256(raw.encode()).hexdigest()[:16]
        key_hash = self._hash_key(raw)
        prefix = raw[:12]
        return raw, key_id, key_hash, prefix

    def _hash_key(self, raw_key: str) -> str:
        """Hash a key for secure storage."""
        if self.master_secret:
            return hmac.new(self.master_secret.encode(), raw_key.encode(), hashlib.sha256).hexdigest()
        return hashlib.sha256(raw_key.encode()).hexdigest()

    def create_key(self, scopes: List[str] = None, rate_limit: int = 100,
                   expiry_days: int = None, description: str = "") -> Tuple[str, APIKey]:
        """Create a new API key. Returns (raw_key, APIKey)."""
        raw, key_id, key_hash, prefix = self._generate_key()
        now = datetime.now()
        expiry = now + timedelta(days=expiry_days or self.DEFAULT_EXPIRY_DAYS)
        
        key = APIKey(
            key_id=key_id,
            key_hash=key_hash,
            prefix=prefix,
            scopes=scopes or ["read"],
            rate_limit=rate_limit,
            created_at=now.isoformat(),
            expires_at=expiry.isoformat(),
            description=description,
        )
        self.keys[key_id] = key
        return raw, key

    def validate_key(self, raw_key: str) -> Tuple[bool, Optional[APIKey], str]:
        """Validate an API key. Returns (valid, key, error_message)."""
        if not raw_key.startswith(self.KEY_PREFIX):
            return False, None, "Invalid key format"

        key_hash = self._hash_key(raw_key)
        
        for key_id, key in self.keys.items():
            if key.key_hash == key_hash:
                if key_id in self._revoked:
                    return False, None, "Key revoked"
                if not key.active:
                    return False, None, "Key inactive"
                if datetime.now() > datetime.fromisoformat(key.expires_at):
                    return False, None, "Key expired"
                
                key.last_used = datetime.now().isoformat()
                key.usage_count += 1
                return True, key, "OK"
        
        return False, None, "Key not found"

    def check_scope(self, key: APIKey, required_scope: str) -> bool:
        """Check if key has required scope."""
        return required_scope in key.scopes or "admin" in key.scopes

    def rotate_key(self, key_id: str) -> Tuple[str, APIKey]:
        """Rotate an existing key. Returns new (raw_key, APIKey)."""
        old_key = self.keys.get(key_id)
        if not old_key:
            raise ValueError(f"Key {key_id} not found")
        
        self._revoked.add(key_id)
        old_key.active = False
        
        raw, new_key = self.create_key(
            scopes=old_key.scopes,
            rate_limit=old_key.rate_limit,
            description=f"Rotated from {key_id[:8]}",
        )
        return raw, new_key

    def revoke_key(self, key_id: str) -> bool:
        """Revoke an API key."""
        if key_id in self.keys:
            self._revoked.add(key_id)
            self.keys[key_id].active = False
            return True
        return False

    def list_keys(self) -> List[Dict]:
        """List all keys (without hashes)."""
        return [
            {
                "key_id": k.key_id[:8] + "...",
                "prefix": k.prefix + "...",
                "scopes": k.scopes,
                "rate_limit": k.rate_limit,
                "active": k.active and k.key_id not in self._revoked,
                "created_at": k.created_at,
                "expires_at": k.expires_at,
                "last_used": k.last_used,
                "usage_count": k.usage_count,
                "description": k.description,
            }
            for k in self.keys.values()
        ]

    def cleanup_expired(self) -> int:
        """Remove expired keys. Returns count removed."""
        now = datetime.now()
        expired = [kid for kid, k in self.keys.items() 
                   if now > datetime.fromisoformat(k.expires_at)]
        for kid in expired:
            del self.keys[kid]
        return len(expired)

    def stats(self) -> Dict:
        active = sum(1 for k in self.keys.values() if k.active and k.key_id not in self._revoked)
        return {
            "total_keys": len(self.keys),
            "active": active,
            "revoked": len(self._revoked),
            "expired": sum(1 for k in self.keys.values()
                          if datetime.now() > datetime.fromisoformat(k.expires_at)),
        }
