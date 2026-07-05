"""URL Shortener — base62 encoding, custom aliases, click analytics, QR code URLs."""
import time
import hashlib
import threading
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict, field
from datetime import datetime
from collections import defaultdict


BASE62_CHARS = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"


def encode_base62(num: int) -> str:
    """Encode an integer to base62 string."""
    if num == 0:
        return BASE62_CHARS[0]
    result = []
    while num > 0:
        result.append(BASE62_CHARS[num % 62])
        num //= 62
    return "".join(reversed(result))


def decode_base62(s: str) -> int:
    """Decode a base62 string to integer."""
    result = 0
    for char in s:
        result = result * 62 + BASE62_CHARS.index(char)
    return result


@dataclass
class ShortURL:
    short_code: str
    original_url: str
    created_at: str
    clicks: int = 0
    custom_alias: bool = False
    expires_at: str = ""
    password: str = ""
    metadata: Dict = field(default_factory=dict)
    click_history: List[Dict] = field(default_factory=list)


class URLShortener:
    """URL shortener with analytics, custom aliases, and expiration."""

    def __init__(self, code_length: int = 6, base_url: str = "https://short.link"):
        self.code_length = code_length
        self.base_url = base_url
        self._urls: Dict[str, ShortURL] = {}
        self._counter = 1000
        self._url_to_code: Dict[str, str] = {}
        self._lock = threading.Lock()

    def shorten(self, url: str, custom_alias: str = None, password: str = "",
                expires_days: int = 0, metadata: Dict = None) -> str:
        """Shorten a URL. Returns the short code."""
        with self._lock:
            # Check if URL already shortened
            if url in self._url_to_code and not custom_alias:
                return self._url_to_code[url]

            # Use custom alias or generate
            if custom_alias:
                if custom_alias in self._urls:
                    raise ValueError(f"Alias '{custom_alias}' already exists")
                code = custom_alias
            else:
                self._counter += 1
                code = encode_base62(self._counter)
                # Pad to minimum length
                while len(code) < self.code_length:
                    code = BASE62_CHARS[0] + code

            expires = ""
            if expires_days != 0:
                from datetime import timedelta
                expires = (datetime.now() + timedelta(days=expires_days)).isoformat()

            short = ShortURL(
                short_code=code,
                original_url=url,
                created_at=datetime.now().isoformat(),
                custom_alias=bool(custom_alias),
                expires_at=expires,
                password=password,
                metadata=metadata or {},
            )
            self._urls[code] = short
            self._url_to_code[url] = code
            return code

    def resolve(self, code: str, password: str = "") -> Optional[str]:
        """Resolve a short code to the original URL. Tracks clicks."""
        with self._lock:
            short = self._urls.get(code)
            if not short:
                return None

            # Check expiration
            if short.expires_at:
                if datetime.now() > datetime.fromisoformat(short.expires_at):
                    return None

            # Check password
            if short.password and short.password != password:
                return None

            # Track click
            short.clicks += 1
            short.click_history.append({
                "timestamp": datetime.now().isoformat(),
                "code": code,
            })

            return short.original_url

    def get_info(self, code: str) -> Optional[Dict]:
        """Get info about a short URL."""
        short = self._urls.get(code)
        if not short:
            return None
        return {
            "short_url": f"{self.base_url}/{code}",
            "original_url": short.original_url,
            "created_at": short.created_at,
            "clicks": short.clicks,
            "custom_alias": short.custom_alias,
            "expires_at": short.expires_at,
            "password_protected": bool(short.password),
        }

    def delete(self, code: str) -> bool:
        """Delete a short URL."""
        with self._lock:
            short = self._urls.pop(code, None)
            if short:
                self._url_to_code.pop(short.original_url, None)
                return True
            return False

    def list_urls(self, limit: int = 100) -> List[Dict]:
        """List all short URLs."""
        return [self.get_info(code) for code in list(self._urls.keys())[:limit]]

    def top_urls(self, n: int = 10) -> List[Dict]:
        """Get most clicked URLs."""
        sorted_urls = sorted(self._urls.values(), key=lambda u: u.clicks, reverse=True)
        return [{"code": u.short_code, "url": u.original_url, "clicks": u.clicks}
                for u in sorted_urls[:n]]

    def qrcode_url(self, code: str, size: str = "200x200") -> Optional[str]:
        """Generate QR code URL using Google Charts API."""
        if code not in self._urls:
            return None
        short_url = f"{self.base_url}/{code}"
        return f"https://chart.googleapis.com/chart?cht=qr&chs={size}&chl={short_url}"

    def is_expired(self, code: str) -> bool:
        short = self._urls.get(code)
        if not short or not short.expires_at:
            return False
        return datetime.now() > datetime.fromisoformat(short.expires_at)

    def cleanup_expired(self) -> int:
        """Remove expired URLs. Returns count removed."""
        expired = [code for code in self._urls if self.is_expired(code)]
        for code in expired:
            self.delete(code)
        return len(expired)

    def stats(self) -> Dict:
        return {
            "total_urls": len(self._urls),
            "total_clicks": sum(u.clicks for u in self._urls.values()),
            "custom_aliases": sum(1 for u in self._urls.values() if u.custom_alias),
            "password_protected": sum(1 for u in self._urls.values() if u.password),
            "expired": sum(1 for code in self._urls if self.is_expired(code)),
        }
