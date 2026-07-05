"""API Rate Limiter Middleware — token bucket + sliding window for FastAPI/Flask/Django."""
import time
import json
from typing import Dict, Optional, Tuple, Callable
from dataclasses import dataclass, field
from collections import defaultdict, deque
import hashlib


@dataclass
class TokenBucket:
    """Token bucket rate limiter — allows bursts up to capacity."""
    capacity: int
    refill_rate: float  # tokens per second
    tokens: float = 0
    last_refill: float = field(default_factory=time.time)

    def __post_init__(self):
        self.tokens = self.capacity

    def consume(self, tokens: int = 1) -> bool:
        self._refill()
        if self.tokens >= tokens:
            self.tokens -= tokens
            return True
        return False

    def _refill(self):
        now = time.time()
        elapsed = now - self.last_refill
        self.tokens = min(self.capacity, self.tokens + elapsed * self.refill_rate)
        self.last_refill = now

    def retry_after(self, tokens: int = 1) -> float:
        self._refill()
        if self.tokens >= tokens:
            return 0.0
        needed = tokens - self.tokens
        return needed / self.refill_rate


@dataclass
class SlidingWindow:
    """Sliding window rate limiter — fixed count per time window."""
    window_seconds: int
    max_requests: int
    requests: deque = field(default_factory=deque)

    def check(self) -> bool:
        now = time.time()
        cutoff = now - self.window_seconds
        while self.requests and self.requests[0] < cutoff:
            self.requests.popleft()
        if len(self.requests) < self.max_requests:
            self.requests.append(now)
            return True
        return False

    def retry_after(self) -> float:
        if not self.requests:
            return 0.0
        return max(0.0, self.requests[0] + self.window_seconds - time.time())


class RateLimiterMiddleware:
    """Multi-strategy rate limiter supporting per-IP, per-user, per-API-key limits."""

    def __init__(self, strategy: str = "token_bucket", default_limit: int = 100,
                 window_seconds: int = 60, refill_rate: float = 1.0):
        self.strategy = strategy
        self.default_limit = default_limit
        self.window_seconds = window_seconds
        self.refill_rate = refill_rate
        self.limiters: Dict[str, object] = {}
        self.custom_limits: Dict[str, Tuple[int, int]] = {}
        self.key_func: Optional[Callable] = None

    def set_key_func(self, func: Callable[[object], str]):
        """Set custom key extraction function (e.g., API key, user ID)."""
        self.key_func = func

    def set_limit(self, key: str, limit: int, window: int = 60):
        """Set custom limit for a specific key (user/IP/api_key)."""
        self.custom_limits[key] = (limit, window)

    def _get_limiter(self, key: str):
        if key in self.limiters:
            return self.limiters[key]

        if key in self.custom_limits:
            limit, window = self.custom_limits[key]
        else:
            limit, window = self.default_limit, self.window_seconds

        if self.strategy == "token_bucket":
            limiter = TokenBucket(capacity=limit, refill_rate=self.refill_rate)
        else:
            limiter = SlidingWindow(window_seconds=window, max_requests=limit)

        self.limiters[key] = limiter
        return limiter

    def check(self, key: str) -> Tuple[bool, float, Dict]:
        """Check if request is allowed. Returns (allowed, retry_after, headers)."""
        limiter = self._get_limiter(key)

        if self.strategy == "token_bucket":
            allowed = limiter.consume(1)
            retry = limiter.retry_after(1) if not allowed else 0.0
            remaining = int(limiter.tokens)
        else:
            allowed = limiter.check()
            retry = limiter.retry_after() if not allowed else 0.0
            remaining = limiter.max_requests - len(limiter.requests)

        return allowed, retry, {
            "X-RateLimit-Limit": str(self.default_limit),
            "X-RateLimit-Remaining": str(max(0, remaining)),
            "X-RateLimit-Reset": str(int(time.time() + (retry if retry > 0 else self.window_seconds))),
        }

    def fastapi_middleware(self):
        """Return FastAPI/Starlette middleware callable."""
        async def middleware(request, call_next):
            key = self.key_func(request) if self.key_func else request.client.host
            allowed, retry_after, headers = self.check(key)
            if not allowed:
                from starlette.responses import JSONResponse
                response = JSONResponse(
                    status_code=429,
                    content={"error": "rate_limited", "retry_after": retry_after},
                )
                for k, v in headers.items():
                    response.headers[k] = v
                return response
            response = await call_next(request)
            for k, v in headers.items():
                response.headers[k] = v
            return response
        return middleware

    def flask_before_request(self):
        """Return Flask before_request callable."""
        def before_request():
            from flask import request, jsonify
            key = self.key_func(request) if self.key_func else request.remote_addr
            allowed, retry_after, headers = self.check(key)
            if not allowed:
                response = jsonify({"error": "rate_limited", "retry_after": retry_after})
                response.status_code = 429
                for k, v in headers.items():
                    response.headers[k] = v
                return response
        return before_request

    def stats(self) -> Dict:
        """Get rate limiter statistics."""
        return {
            "strategy": self.strategy,
            "tracked_keys": len(self.limiters),
            "custom_limits": len(self.custom_limits),
            "default_limit": self.default_limit,
        }
