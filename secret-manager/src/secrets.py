"""Secret Manager — encrypted secret storage with .env management and rotation tracking."""
import os
import json
import base64
import hashlib
import hmac
import time
import secrets as _pysecrets
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict, field
from datetime import datetime, timedelta
from pathlib import Path
from cryptography.fernet import Fernet
import threading


@dataclass
class Secret:
    key: str
    encrypted_value: str
    version: int = 1
    created_at: str = ""
    updated_at: str = ""
    expires_at: str = ""
    rotated_at: str = ""
    rotation_days: int = 0
    metadata: Dict = field(default_factory=dict)
    tags: List[str] = field(default_factory=list)


class SecretManager:
    """Manage application secrets with encryption, rotation, and .env integration."""

    def __init__(self, master_key: str = None):
        if master_key:
            key = hashlib.sha256(master_key.encode()).digest()
            self._fernet = Fernet(base64.urlsafe_b64encode(key))
        else:
            self._fernet = Fernet(Fernet.generate_key())
        self._secrets: Dict[str, Secret] = {}
        self._lock = threading.RLock()
        self._history: List[Dict] = []

    def set_secret(self, key: str, value: str, rotation_days: int = 0,
                   tags: List[str] = None, metadata: Dict = None) -> Secret:
        """Store an encrypted secret."""
        with self._lock:
            now = datetime.now().isoformat()
            existing = self._secrets.get(key)
            version = existing.version + 1 if existing else 1

            encrypted = self._fernet.encrypt(value.encode()).decode()
            expires = (datetime.now() + timedelta(days=rotation_days)).isoformat() if rotation_days else ""

            secret = Secret(
                key=key,
                encrypted_value=encrypted,
                version=version,
                created_at=existing.created_at if existing else now,
                updated_at=now,
                expires_at=expires,
                rotation_days=rotation_days,
                metadata=metadata or {},
                tags=tags or [],
            )
            self._secrets[key] = secret
            self._history.append({"action": "set", "key": key, "version": version, "timestamp": now})
            return secret

    def get_secret(self, key: str) -> Optional[str]:
        """Retrieve and decrypt a secret."""
        with self._lock:
            secret = self._secrets.get(key)
            if not secret:
                return None
            return self._fernet.decrypt(secret.encrypted_value.encode()).decode()

    def delete_secret(self, key: str) -> bool:
        """Delete a secret."""
        with self._lock:
            if key in self._secrets:
                del self._secrets[key]
                self._history.append({"action": "delete", "key": key, "timestamp": datetime.now().isoformat()})
                return True
            return False

    def rotate_secret(self, key: str, new_value: str = None) -> Optional[Secret]:
        """Rotate a secret. Generates new value if not provided."""
        with self._lock:
            existing = self._secrets.get(key)
            if not existing:
                return None
            if new_value is None:
                new_value = base64.urlsafe_b64encode(os.urandom(32)).decode()
            secret = self.set_secret(key, new_value, rotation_days=existing.rotation_days,
                                     tags=existing.tags, metadata=existing.metadata)
            secret.rotated_at = datetime.now().isoformat()
            self._history.append({"action": "rotate", "key": key, "version": secret.version,
                                  "timestamp": secret.rotated_at})
            return secret

    def needs_rotation(self, key: str) -> bool:
        """Check if a secret needs rotation."""
        with self._lock:
            secret = self._secrets.get(key)
            if not secret or not secret.rotation_days:
                return False
            if not secret.expires_at:
                return False
            return datetime.now() > datetime.fromisoformat(secret.expires_at)

    def list_secrets(self) -> List[Dict]:
        """List all secrets (without values)."""
        with self._lock:
            return [
                {
                    "key": s.key,
                    "version": s.version,
                    "updated_at": s.updated_at,
                    "expires_at": s.expires_at,
                    "rotation_days": s.rotation_days,
                    "needs_rotation": self.needs_rotation(s.key),
                    "tags": s.tags,
                }
                for s in self._secrets.values()
            ]

    def export_env(self, keys: List[str] = None) -> str:
        """Export secrets as .env file format."""
        with self._lock:
            lines = []
            target_keys = keys or list(self._secrets.keys())
            for key in target_keys:
                secret = self._secrets.get(key)
                if secret:
                    value = self.get_secret(key)
                    env_key = key.upper().replace(".", "_")
                    lines.append(f"{env_key}={value}")
            return "\n".join(lines)

    def load_env_file(self, filepath: str, overwrite: bool = False) -> int:
        """Load secrets from a .env file."""
        count = 0
        with open(filepath) as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if "=" in line:
                    key, value = line.split("=", 1)
                    key = key.strip()
                    value = value.strip().strip('"').strip("'")
                    if overwrite or key not in self._secrets:
                        self.set_secret(key.lower().replace("_", "."), value)
                        count += 1
        return count

    def export_json(self) -> str:
        """Export secrets metadata as JSON (no values)."""
        with self._lock:
            return json.dumps([{
                "key": s.key, "version": s.version,
                "created_at": s.created_at, "updated_at": s.updated_at,
                "rotation_days": s.rotation_days, "tags": s.tags,
            } for s in self._secrets.values()], indent=2)

    def stats(self) -> Dict:
        return {
            "total_secrets": len(self._secrets),
            "needs_rotation": sum(1 for s in self._secrets.values() if self.needs_rotation(s.key)),
            "total_versions": sum(s.version for s in self._secrets.values()),
            "history_entries": len(self._history),
        }
