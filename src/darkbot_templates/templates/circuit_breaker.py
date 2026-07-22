"""Circuit Breaker pattern — fail-fast when downstream is unhealthy.

Usage:
    cb = CircuitBreaker(failure_threshold=5, recovery_timeout=30.0)
    if cb.allow():
        try:
            result = call_downstream()
            cb.success()
        except Exception:
            cb.failure()
    else:
        result = None  # fast-fail
"""

import time
import threading


class CircuitBreaker:
    """State machine: CLOSED -> OPEN (on threshold) -> HALF_OPEN (after timeout) -> CLOSED."""

    CLOSED = "CLOSED"
    OPEN = "OPEN"
    HALF_OPEN = "HALF_OPEN"

    def __init__(self, failure_threshold: int = 5, recovery_timeout: float = 30.0) -> None:
        self._failure_threshold = failure_threshold
        self._recovery_timeout = recovery_timeout
        self._failures = 0
        self._state = self.CLOSED
        self._last_failure_time = 0.0
        self._lock = threading.Lock()

    @property
    def state(self) -> str:
        with self._lock:
            if self._state == self.OPEN and time.monotonic() - self._last_failure_time >= self._recovery_timeout:
                self._state = self.HALF_OPEN
                self._failures = 0
            return self._state

    def allow(self) -> bool:
        return self.state != self.OPEN

    def success(self) -> None:
        with self._lock:
            self._failures = 0
            self._state = self.CLOSED

    def failure(self) -> None:
        with self._lock:
            self._failures += 1
            self._last_failure_time = time.monotonic()
            if self._failures >= self._failure_threshold:
                self._state = self.OPEN

    def reset(self) -> None:
        with self._lock:
            self._failures = 0
            self._state = self.CLOSED
            self._last_failure_time = 0.0
