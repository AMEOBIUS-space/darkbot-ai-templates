import sys, os, time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from resilience import (RetryCircuitBreaker, RetryConfig, CircuitConfig,
                        BackoffStrategy, CircuitState, CircuitBreaker)


def test_success_first_try():
    rc = RetryCircuitBreaker(RetryConfig(max_attempts=3, base_delay=0.01))
    success, result, attempts = rc.execute(lambda: 42)
    assert success is True
    assert result == 42
    assert len(attempts) == 1

def test_retry_then_success():
    attempts_made = []
    rc = RetryCircuitBreaker(RetryConfig(max_attempts=3, base_delay=0.01))
    def flaky():
        attempts_made.append(1)
        if len(attempts_made) < 3:
            raise ValueError("temp")
        return "ok"
    success, result, attempts = rc.execute(flaky)
    assert success is True
    assert result == "ok"
    assert len(attempts) == 3

def test_all_retries_fail():
    rc = RetryCircuitBreaker(RetryConfig(max_attempts=3, base_delay=0.01))
    success, result, attempts = rc.execute(lambda: (_ for _ in ()).throw(ValueError("fail")))
    assert success is False
    assert len(attempts) == 3

def test_fixed_backoff():
    rc = RetryCircuitBreaker(RetryConfig(strategy=BackoffStrategy.FIXED, base_delay=0.01))
    delays = [rc._calculate_delay(i) for i in range(1, 4)]
    assert all(d == 0.01 for d in delays)

def test_linear_backoff():
    rc = RetryCircuitBreaker(RetryConfig(strategy=BackoffStrategy.LINEAR, base_delay=0.01))
    assert rc._calculate_delay(1) == 0.01
    assert rc._calculate_delay(2) == 0.02
    assert rc._calculate_delay(3) == 0.03

def test_exponential_backoff():
    rc = RetryCircuitBreaker(RetryConfig(strategy=BackoffStrategy.EXPONENTIAL, base_delay=0.01))
    assert rc._calculate_delay(1) == 0.01
    assert rc._calculate_delay(2) == 0.02
    assert rc._calculate_delay(3) == 0.04

def test_max_delay_cap():
    rc = RetryCircuitBreaker(RetryConfig(base_delay=1.0, max_delay=5.0))
    assert rc._calculate_delay(10) == 5.0

def test_circuit_opens():
    cb = CircuitBreaker(CircuitConfig(failure_threshold=3))
    cb.record_failure()
    cb.record_failure()
    cb.record_failure()
    assert cb.state == CircuitState.OPEN
    assert cb.can_execute() is False

def test_circuit_recovery():
    cb = CircuitBreaker(CircuitConfig(failure_threshold=2, recovery_timeout=0.1))
    cb.record_failure()
    cb.record_failure()
    assert cb.state == CircuitState.OPEN
    time.sleep(0.15)
    assert cb.can_execute() is True
    assert cb.state == CircuitState.HALF_OPEN

def test_circuit_half_open_to_closed():
    cb = CircuitBreaker(CircuitConfig(failure_threshold=2, recovery_timeout=0.1, success_threshold=2))
    cb.record_failure()
    cb.record_failure()
    time.sleep(0.15)
    cb.can_execute()
    cb.record_success()
    cb.record_success()
    assert cb.state == CircuitState.CLOSED

def test_circuit_half_open_to_open():
    cb = CircuitBreaker(CircuitConfig(failure_threshold=2, recovery_timeout=0.1))
    cb.record_failure()
    cb.record_failure()
    time.sleep(0.15)
    cb.can_execute()
    cb.record_failure()
    assert cb.state == CircuitState.OPEN

def test_circuit_reset():
    cb = CircuitBreaker()
    cb.record_failure()
    cb.record_failure()
    cb.reset()
    assert cb.state == CircuitState.CLOSED
    assert cb._failure_count == 0

def test_combined_circuit_blocks():
    rc = RetryCircuitBreaker(
        RetryConfig(max_attempts=1, base_delay=0.01),
        CircuitConfig(failure_threshold=2, recovery_timeout=60)
    )
    rc.execute(lambda: (_ for _ in ()).throw(ValueError("fail")))
    rc.execute(lambda: (_ for _ in ()).throw(ValueError("fail")))
    success, _, attempts = rc.execute(lambda: "should not reach")
    assert success is False
    assert "Circuit breaker" in attempts[-1].error

def test_stats():
    rc = RetryCircuitBreaker(RetryConfig(max_attempts=2, base_delay=0.01))
    rc.execute(lambda: 42)
    stats = rc.stats()
    assert stats["successful"] == 1
    assert stats["circuit"]["state"] == "closed"

def test_get_history():
    rc = RetryCircuitBreaker(RetryConfig(max_attempts=1))
    rc.execute(lambda: 1)
    history = rc.get_history()
    assert len(history) == 1
    assert history[0].success is True

def test_non_retryable_exception():
    rc = RetryCircuitBreaker(RetryConfig(max_attempts=3, base_delay=0.01, retry_on=(ValueError,)))
    success, _, attempts = rc.execute(lambda: (_ for _ in ()).throw(TypeError("not retryable")))
    assert success is False
    assert len(attempts) == 1
