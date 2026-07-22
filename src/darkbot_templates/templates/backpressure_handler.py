from __future__ import annotations

"""Backpressure handler — shed load when queue depth exceeds threshold.

Usage:
    bp = BackpressureHandler(max_depth=1000, shed_ratio=0.5)
    if bp.should_accept():
        process(item)
    else:
        bp.shed()  # drop or defer
"""

import threading
import time
from collections import deque


class BackpressureHandler:
    """Tracks queue depth and decides whether to accept or shed items."""

    def __init__(self, max_depth: int = 1000, shed_ratio: float = 0.8) -> None:
        self._max_depth = max_depth
        self._shed_threshold = int(max_depth * shed_ratio)
        self._depth = 0
        self._shed_count = 0
        self._accept_count = 0
        self._lock = threading.Lock()
        self._history = deque(maxlen=60)

    def should_accept(self) -> bool:
        with self._lock:
            return self._depth < self._shed_threshold

    def accept(self) -> None:
        with self._lock:
            self._depth += 1
            self._accept_count += 1

    def complete(self) -> None:
        with self._lock:
            self._depth = max(0, self._depth - 1)

    def shed(self) -> None:
        with self._lock:
            self._shed_count += 1
            self._history.append(("shed", time.monotonic()))

    @property
    def depth(self) -> int:
        with self._lock:
            return self._depth

    @property
    def stats(self) -> dict:
        with self._lock:
            return {
                "depth": self._depth,
                "max_depth": self._max_depth,
                "shed_threshold": self._shed_threshold,
                "accepted": self._accept_count,
                "shed": self._shed_count,
                "shed_ratio": self._shed_count / max(1, self._accept_count + self._shed_count),
            }
