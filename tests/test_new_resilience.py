"""Tests for CircuitBreaker, BackpressureHandler, ServiceRegistry."""
from __future__ import annotations

import time

from darkbot_templates import (
    BackpressureHandler,
    CircuitBreaker,
    ServiceRegistry,
)


class TestCircuitBreaker:
    def test_starts_closed(self):
        cb = CircuitBreaker(failure_threshold=3, recovery_timeout=5.0)
        assert cb.state == "CLOSED"
        assert cb.allow() is True

    def test_opens_after_threshold(self):
        cb = CircuitBreaker(failure_threshold=3, recovery_timeout=30.0)
        cb.failure()
        cb.failure()
        assert cb.state == "CLOSED"
        cb.failure()
        assert cb.state == "OPEN"
        assert cb.allow() is False

    def test_half_open_after_timeout(self):
        cb = CircuitBreaker(failure_threshold=2, recovery_timeout=0.1)
        cb.failure()
        cb.failure()
        assert cb.state == "OPEN"
        time.sleep(0.15)
        assert cb.state == "HALF_OPEN"
        assert cb.allow() is True

    def test_success_resets(self):
        cb = CircuitBreaker(failure_threshold=3, recovery_timeout=30.0)
        cb.failure()
        cb.failure()
        cb.success()
        assert cb.state == "CLOSED"

    def test_reset_clears_all(self):
        cb = CircuitBreaker(failure_threshold=2, recovery_timeout=30.0)
        cb.failure()
        cb.failure()
        cb.reset()
        assert cb.state == "CLOSED"
        assert cb.allow() is True


class TestBackpressureHandler:
    def test_starts_empty(self):
        bp = BackpressureHandler(max_depth=10, shed_ratio=0.8)
        assert bp.depth == 0
        assert bp.should_accept() is True

    def test_blocks_at_shed_threshold(self):
        bp = BackpressureHandler(max_depth=10, shed_ratio=0.8)
        for _ in range(8):
            bp.accept()
        assert bp.should_accept() is False

    def test_complete_decrements(self):
        bp = BackpressureHandler(max_depth=10, shed_ratio=0.8)
        bp.accept()
        bp.accept()
        bp.complete()
        assert bp.depth == 1

    def test_shed_increments(self):
        bp = BackpressureHandler(max_depth=10, shed_ratio=0.8)
        bp.shed()
        bp.shed()
        assert bp.stats["shed"] == 2

    def test_stats_report_ratio(self):
        bp = BackpressureHandler(max_depth=10, shed_ratio=0.5)
        bp.accept()
        bp.shed()
        s = bp.stats
        assert s["accepted"] == 1
        assert s["shed"] == 1
        assert 0 < s["shed_ratio"] < 1


class TestServiceRegistry:
    def test_empty_returns_none(self):
        reg = ServiceRegistry()
        assert reg.get("nope") is None

    def test_round_robin(self):
        reg = ServiceRegistry()
        reg.register("api", "http://a")
        reg.register("api", "http://b")
        results = [reg.get("api") for _ in range(4)]
        assert results == ["http://a", "http://b", "http://a", "http://b"]

    def test_deregister(self):
        reg = ServiceRegistry()
        reg.register("api", "http://a")
        reg.register("api", "http://b")
        reg.deregister("api", "http://a")
        assert reg.list("api") == ["http://b"]

    def test_no_duplicate(self):
        reg = ServiceRegistry()
        reg.register("api", "http://a")
        reg.register("api", "http://a")
        assert reg.list("api") == ["http://a"]

    def test_services_dict(self):
        reg = ServiceRegistry()
        reg.register("api", "http://a")
        reg.register("db", "http://db1")
        s = reg.services
        assert "api" in s
        assert "db" in s
