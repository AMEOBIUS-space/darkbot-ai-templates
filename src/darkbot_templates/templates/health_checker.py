from __future__ import annotations

"""Health checker — probe endpoints and track availability.

Usage:
    hc = HealthChecker(timeout=5.0)
    result = hc.check("https://api.example.com/health")
    # result = {"url": ..., "status": "up"|"down", "latency_ms": ..., "status_code": ...}
"""

import socket
import time
import urllib.error
import urllib.request
from typing import Optional


class HealthChecker:
    """HTTP health probe with latency tracking."""

    def __init__(self, timeout: float = 5.0) -> None:
        self._timeout = timeout
        self._history: list[dict] = []

    def check(self, url: str) -> dict:
        start = time.monotonic()
        result: dict = {
            "url": url,
            "status": "down",
            "latency_ms": 0.0,
            "status_code": None,
            "error": None,
        }
        try:
            req = urllib.request.Request(url, method="GET")
            with urllib.request.urlopen(req, timeout=self._timeout) as resp:
                result["status_code"] = resp.status
                result["status"] = "up" if resp.status < 500 else "degraded"
        except urllib.error.HTTPError as e:
            result["status_code"] = e.code
            result["status"] = "degraded" if e.code < 500 else "down"
            result["error"] = str(e)
        except (urllib.error.URLError, socket.timeout, OSError) as e:
            result["error"] = type(e).__name__
        result["latency_ms"] = round((time.monotonic() - start) * 1000, 1)
        self._history.append(result)
        if len(self._history) > 100:
            self._history = self._history[-100:]
        return result

    @property
    def history(self) -> list[dict]:
        return list(self._history)

    @property
    def uptime_percentage(self) -> float:
        if not self._history:
            return 0.0
        up = sum(1 for h in self._history if h["status"] == "up")
        return round(up / len(self._history) * 100, 1)

    def reset(self) -> None:
        self._history.clear()
