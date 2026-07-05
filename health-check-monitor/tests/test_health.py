import sys, os, time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from health import HealthMonitor, HealthCheck, CircuitBreaker, ServiceStatus, CircuitState


def test_circuit_breaker_closed():
    cb = CircuitBreaker(failure_threshold=3)
    assert cb.state == CircuitState.CLOSED
    assert cb.can_execute() is True


def test_circuit_breaker_opens():
    cb = CircuitBreaker(failure_threshold=3)
    cb.record_failure()
    cb.record_failure()
    cb.record_failure()
    assert cb.state == CircuitState.OPEN
    assert cb.can_execute() is False


def test_circuit_breaker_recovery():
    cb = CircuitBreaker(failure_threshold=2, recovery_timeout=0.1)
    cb.record_failure()
    cb.record_failure()
    assert cb.state == CircuitState.OPEN
    time.sleep(0.15)
    assert cb.can_execute() is True
    assert cb.state == CircuitState.HALF_OPEN


def test_circuit_breaker_half_open_to_closed():
    cb = CircuitBreaker(failure_threshold=2, recovery_timeout=0.1, half_open_max_calls=2)
    cb.record_failure()
    cb.record_failure()
    time.sleep(0.15)
    cb.can_execute()  # Transitions to half_open
    cb.record_success()
    cb.record_success()
    assert cb.state == CircuitState.CLOSED


def test_circuit_breaker_half_open_to_open():
    cb = CircuitBreaker(failure_threshold=2, recovery_timeout=0.1)
    cb.record_failure()
    cb.record_failure()
    time.sleep(0.15)
    cb.can_execute()  # half_open
    cb.record_failure()
    assert cb.state == CircuitState.OPEN


def test_add_check():
    mon = HealthMonitor()
    mon.add_check("api", "https://api.example.com/health")
    assert "api" in mon.checks
    assert mon.checks["api"].url == "https://api.example.com/health"


def test_overall_status_empty():
    mon = HealthMonitor()
    assert mon.overall_status() == ServiceStatus.UNKNOWN


def test_overall_status_healthy():
    mon = HealthMonitor()
    mon.add_check("a", "https://a.com")
    mon.add_check("b", "https://b.com")
    mon.checks["a"].last_status = ServiceStatus.HEALTHY
    mon.checks["b"].last_status = ServiceStatus.HEALTHY
    assert mon.overall_status() == ServiceStatus.HEALTHY


def test_overall_status_unhealthy():
    mon = HealthMonitor()
    mon.add_check("a", "https://a.com")
    mon.add_check("b", "https://b.com")
    mon.checks["a"].last_status = ServiceStatus.HEALTHY
    mon.checks["b"].last_status = ServiceStatus.UNHEALTHY
    assert mon.overall_status() == ServiceStatus.UNHEALTHY


def test_overall_status_degraded():
    mon = HealthMonitor()
    mon.add_check("a", "https://a.com")
    mon.add_check("b", "https://b.com")
    mon.checks["a"].last_status = ServiceStatus.HEALTHY
    mon.checks["b"].last_status = ServiceStatus.DEGRADED
    assert mon.overall_status() == ServiceStatus.DEGRADED


def test_alert_handler():
    mon = HealthMonitor()
    alerts = []
    mon.add_alert_handler(lambda a: alerts.append(a))
    mon.add_check("api", "https://nonexistent.invalid", timeout=1)
    mon.check_service("api")
    assert len(alerts) >= 1
    assert alerts[0]["service"] == "api"


def test_stats():
    mon = HealthMonitor()
    mon.add_check("a", "https://a.com")
    mon.add_check("b", "https://b.com")
    mon.checks["a"].last_status = ServiceStatus.HEALTHY
    mon.checks["b"].last_status = ServiceStatus.UNHEALTHY
    stats = mon.stats()
    assert stats["services"] == 2
    assert stats["healthy"] == 1
    assert stats["unhealthy"] == 1


def test_circuit_stats():
    cb = CircuitBreaker(failure_threshold=5)
    cb.record_failure()
    cb.record_failure()
    stats = cb.stats()
    assert stats["failures"] == 2
    assert stats["state"] == "closed"


def test_history_limit():
    mon = HealthMonitor()
    mon.history_limit = 3
    mon.add_check("api", "https://nonexistent.invalid", timeout=1)
    for _ in range(5):
        mon.check_service("api")
    assert len(mon.checks["api"].history) <= 3
