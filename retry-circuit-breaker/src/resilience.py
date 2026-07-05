"""Retry & Circuit Breaker — combined resilience patterns with backoff strategies."""
import time
import random
import threading
from typing import Callable, Optional, Dict, List, Any, Tuple
from dataclasses import dataclass, asdict, field
from datetime import datetime
from enum import Enum


class BackoffStrategy(Enum):
    FIXED = "fixed"
    LINEAR = "linear"
    EXPONENTIAL = "exponential"
    EXPONENTIAL_JITTER = "exponential_jitter"


class CircuitState(Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


@dataclass
class RetryConfig:
    max_attempts: int = 3
    base_delay: float = 1.0
    max_delay: float = 60.0
    strategy: BackoffStrategy = BackoffStrategy.EXPONENTIAL
    retry_on: tuple = (Exception,)
    retry_on_status: List[int] = field(default_factory=list)


@dataclass
class CircuitConfig:
    failure_threshold: int = 5
    recovery_timeout: float = 60.0
    half_open_max_calls: int = 3
    success_threshold: int = 2


@dataclass
class AttemptResult:
    attempt: int
    success: bool
    error: str = ""
    duration: float = 0.0
    delay_before_next: float = 0.0


class CircuitBreaker:
    def __init__(self, config: CircuitConfig = None):
        self.config = config or CircuitConfig()
        self.state = CircuitState.CLOSED
        self._failure_count = 0
        self._success_count = 0
        self._last_failure_time = 0.0
        self._half_open_calls = 0
        self._lock = threading.Lock()

    def can_execute(self) -> bool:
        with self._lock:
            if self.state == CircuitState.CLOSED:
                return True
            if self.state == CircuitState.OPEN:
                if time.time() - self._last_failure_time > self.config.recovery_timeout:
                    self.state = CircuitState.HALF_OPEN
                    self._half_open_calls = 0
                    self._success_count = 0
                    return True
                return False
            if self.state == CircuitState.HALF_OPEN:
                if self._half_open_calls < self.config.half_open_max_calls:
                    self._half_open_calls += 1
                    return True
                return False
            return False

    def record_success(self):
        with self._lock:
            self._success_count += 1
            self._failure_count = 0
            if self.state == CircuitState.HALF_OPEN:
                if self._success_count >= self.config.success_threshold:
                    self.state = CircuitState.CLOSED
            elif self.state == CircuitState.OPEN:
                self.state = CircuitState.HALF_OPEN

    def record_failure(self):
        with self._lock:
            self._failure_count += 1
            self._success_count = 0
            self._last_failure_time = time.time()
            if self.state == CircuitState.HALF_OPEN:
                self.state = CircuitState.OPEN
            elif self._failure_count >= self.config.failure_threshold:
                self.state = CircuitState.OPEN

    def reset(self):
        with self._lock:
            self.state = CircuitState.CLOSED
            self._failure_count = 0
            self._success_count = 0
            self._half_open_calls = 0

    def stats(self) -> Dict:
        return {"state": self.state.value, "failures": self._failure_count,
                "successes": self._success_count, "threshold": self.config.failure_threshold}


class RetryCircuitBreaker:
    def __init__(self, retry_config: RetryConfig = None, circuit_config: CircuitConfig = None):
        self.retry_config = retry_config or RetryConfig()
        self.circuit = CircuitBreaker(circuit_config)
        self._results: List[AttemptResult] = []
        self._lock = threading.Lock()

    def _calculate_delay(self, attempt: int) -> float:
        s = self.retry_config.strategy
        base = self.retry_config.base_delay
        max_d = self.retry_config.max_delay
        if s == BackoffStrategy.FIXED:
            return min(base, max_d)
        elif s == BackoffStrategy.LINEAR:
            return min(base * attempt, max_d)
        elif s == BackoffStrategy.EXPONENTIAL:
            return min(base * (2 ** (attempt - 1)), max_d)
        elif s == BackoffStrategy.EXPONENTIAL_JITTER:
            delay = min(base * (2 ** (attempt - 1)), max_d)
            return min(delay + random.uniform(0, delay * 0.1), max_d)
        return base

    def execute(self, func: Callable, *args, **kwargs) -> Tuple[bool, Any, List[AttemptResult]]:
        results = []
        for attempt in range(1, self.retry_config.max_attempts + 1):
            if not self.circuit.can_execute():
                results.append(AttemptResult(attempt=attempt, success=False,
                    error=f"Circuit breaker {self.circuit.state.value}"))
                with self._lock:
                    self._results.extend(results)
                return False, None, results
            start = time.time()
            try:
                result = func(*args, **kwargs)
                duration = time.time() - start
                self.circuit.record_success()
                results.append(AttemptResult(attempt=attempt, success=True, duration=duration))
                with self._lock:
                    self._results.extend(results)
                return True, result, results
            except self.retry_config.retry_on as e:
                duration = time.time() - start
                self.circuit.record_failure()
                delay = self._calculate_delay(attempt) if attempt < self.retry_config.max_attempts else 0
                results.append(AttemptResult(attempt=attempt, success=False, error=str(e),
                    duration=duration, delay_before_next=delay))
                if attempt < self.retry_config.max_attempts and delay > 0:
                    time.sleep(delay)
            except Exception as e:
                duration = time.time() - start
                self.circuit.record_failure()
                results.append(AttemptResult(attempt=attempt, success=False, error=str(e), duration=duration))
                with self._lock:
                    self._results.extend(results)
                return False, None, results
        with self._lock:
            self._results.extend(results)
        return False, None, results

    def get_history(self) -> List[AttemptResult]:
        return self._results

    def stats(self) -> Dict:
        return {"circuit": self.circuit.stats(), "total_attempts": len(self._results),
                "successful": sum(1 for r in self._results if r.success),
                "failed": sum(1 for r in self._results if not r.success),
                "retry_config": {"max_attempts": self.retry_config.max_attempts,
                    "strategy": self.retry_config.strategy.value, "base_delay": self.retry_config.base_delay}}
