from __future__ import annotations

"""Service registry — track service instances for client-side load balancing.

Usage:
    reg = ServiceRegistry()
    reg.register("api", "http://node1:8080")
    reg.register("api", "http://node2:8080")
    endpoint = reg.get("api")  # round-robin
"""

import itertools
import threading
from collections import defaultdict


class ServiceRegistry:
    """In-memory service registry with round-robin selection."""

    def __init__(self) -> None:
        self._services: dict[str, list[str]] = defaultdict(list)
        self._cycles: dict[str, itertools.cycle] = {}
        self._lock = threading.Lock()

    def register(self, name: str, endpoint: str) -> None:
        with self._lock:
            if endpoint not in self._services[name]:
                self._services[name].append(endpoint)
                self._cycles[name] = itertools.cycle(self._services[name])

    def deregister(self, name: str, endpoint: str) -> None:
        with self._lock:
            if endpoint in self._services[name]:
                self._services[name].remove(endpoint)
                if self._services[name]:
                    self._cycles[name] = itertools.cycle(self._services[name])
                else:
                    self._cycles.pop(name, None)

    def get(self, name: str) -> str | None:
        with self._lock:
            if name not in self._cycles:
                return None
            return next(self._cycles[name])

    def list(self, name: str) -> list[str]:
        with self._lock:
            return list(self._services.get(name, []))

    @property
    def services(self) -> dict[str, list[str]]:
        with self._lock:
            return {k: list(v) for k, v in self._services.items()}
