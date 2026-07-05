"""Health Check Monitor — HTTP endpoint monitoring with circuit breaker and alerting."""
import time
import json
import urllib.request
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass, asdict, field
from datetime import datetime
from enum import Enum


class ServiceStatus(Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


class CircuitState(Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


@dataclass
class HealthCheck:
    name: str
    url: str
    method: str = "GET"
    timeout: int = 10
    expected_status: int = 200
    expected_body: str = ""
    interval: int = 60  # seconds between checks
    last_check: str = ""
    last_status: ServiceStatus = ServiceStatus.UNKNOWN
    last_response_time: float = 0.0
    consecutive_failures: int = 0
    consecutive_successes: int = 0
    history: List[Dict] = field(default_factory=list)


class CircuitBreaker:
    """Circuit breaker for health checks."""

    def __init__(self, failure_threshold: int = 5, recovery_timeout: int = 60,
                 half_open_max_calls: int = 3):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.half_open_max_calls = half_open_max_calls
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time = 0.0
        self.half_open_calls = 0

    def record_success(self):
        self.success_count += 1
        self.failure_count = 0
        if self.state == CircuitState.HALF_OPEN:
            if self.success_count >= self.half_open_max_calls:
                self.state = CircuitState.CLOSED
                self.half_open_calls = 0
        elif self.state == CircuitState.OPEN:
            self.state = CircuitState.HALF_OPEN

    def record_failure(self):
        self.failure_count += 1
        self.success_count = 0
        self.last_failure_time = time.time()
        if self.state == CircuitState.HALF_OPEN:
            self.state = CircuitState.OPEN
        elif self.failure_count >= self.failure_threshold:
            self.state = CircuitState.OPEN

    def can_execute(self) -> bool:
        if self.state == CircuitState.CLOSED:
            return True
        if self.state == CircuitState.OPEN:
            if time.time() - self.last_failure_time > self.recovery_timeout:
                self.state = CircuitState.HALF_OPEN
                self.half_open_calls = 0
                return True
            return False
        if self.state == CircuitState.HALF_OPEN:
            if self.half_open_calls < self.half_open_max_calls:
                self.half_open_calls += 1
                return True
            return False
        return False

    def stats(self) -> Dict:
        return {
            "state": self.state.value,
            "failures": self.failure_count,
            "successes": self.success_count,
            "threshold": self.failure_threshold,
        }


class HealthMonitor:
    """Monitor service health with circuit breaker and alerting."""

    def __init__(self):
        self.checks: Dict[str, HealthCheck] = {}
        self.circuits: Dict[str, CircuitBreaker] = {}
        self.alerts: List[Dict] = []
        self.alert_handlers: List[Callable] = []
        self.history_limit = 100

    def add_check(self, name: str, url: str, **kwargs) -> HealthCheck:
        check = HealthCheck(name=name, url=url, **kwargs)
        self.checks[name] = check
        self.circuits[name] = CircuitBreaker(
            failure_threshold=kwargs.get("failure_threshold", 5),
            recovery_timeout=kwargs.get("recovery_timeout", 60),
        )
        return check

    def add_alert_handler(self, handler: Callable):
        self.alert_handlers.append(handler)

    def check_service(self, name: str) -> HealthCheck:
        """Perform a health check on a single service."""
        check = self.checks.get(name)
        if not check:
            raise ValueError(f"Unknown check: {name}")

        circuit = self.circuits[name]
        if not circuit.can_execute():
            check.last_status = ServiceStatus.UNHEALTHY
            return check

        start = time.time()
        try:
            req = urllib.request.Request(check.url, method=check.method)
            resp = urllib.request.urlopen(req, timeout=check.timeout)
            elapsed = time.time() - start
            status_code = resp.getcode()
            body = resp.read().decode("utf-8", errors="replace")

            check.last_response_time = elapsed
            check.last_check = datetime.now().isoformat()

            if status_code == check.expected_status:
                if check.expected_body and check.expected_body not in body:
                    check.last_status = ServiceStatus.DEGRADED
                    circuit.record_failure()
                else:
                    check.last_status = ServiceStatus.HEALTHY
                    circuit.record_success()
                    check.consecutive_successes += 1
                    check.consecutive_failures = 0
            else:
                check.last_status = ServiceStatus.UNHEALTHY
                circuit.record_failure()
                check.consecutive_failures += 1
                check.consecutive_successes = 0
                self._alert(name, "unhealthy_status", f"Expected {check.expected_status}, got {status_code}")

        except urllib.error.HTTPError as e:
            elapsed = time.time() - start
            check.last_response_time = elapsed
            check.last_status = ServiceStatus.UNHEALTHY
            check.last_check = datetime.now().isoformat()
            circuit.record_failure()
            check.consecutive_failures += 1
            check.consecutive_successes = 0
            self._alert(name, "http_error", str(e))

        except Exception as e:
            elapsed = time.time() - start
            check.last_response_time = elapsed
            check.last_status = ServiceStatus.UNHEALTHY
            check.last_check = datetime.now().isoformat()
            circuit.record_failure()
            check.consecutive_failures += 1
            check.consecutive_successes = 0
            self._alert(name, "connection_error", str(e))

        # Record history
        check.history.append({
            "timestamp": check.last_check,
            "status": check.last_status.value,
            "response_time": check.last_response_time,
        })
        if len(check.history) > self.history_limit:
            check.history = check.history[-self.history_limit:]

        return check

    def _alert(self, service: str, alert_type: str, message: str):
        alert = {
            "service": service,
            "type": alert_type,
            "message": message,
            "timestamp": datetime.now().isoformat(),
        }
        self.alerts.append(alert)
        for handler in self.alert_handlers:
            try:
                handler(alert)
            except Exception:
                pass

    def check_all(self) -> Dict[str, HealthCheck]:
        """Check all registered services."""
        return {name: self.check_service(name) for name in self.checks}

    def overall_status(self) -> ServiceStatus:
        """Get overall system health status."""
        if not self.checks:
            return ServiceStatus.UNKNOWN
        statuses = [c.last_status for c in self.checks.values()]
        if all(s == ServiceStatus.HEALTHY for s in statuses):
            return ServiceStatus.HEALTHY
        if any(s == ServiceStatus.UNHEALTHY for s in statuses):
            return ServiceStatus.UNHEALTHY
        return ServiceStatus.DEGRADED

    def stats(self) -> Dict:
        return {
            "services": len(self.checks),
            "healthy": sum(1 for c in self.checks.values() if c.last_status == ServiceStatus.HEALTHY),
            "unhealthy": sum(1 for c in self.checks.values() if c.last_status == ServiceStatus.UNHEALTHY),
            "degraded": sum(1 for c in self.checks.values() if c.last_status == ServiceStatus.DEGRADED),
            "overall": self.overall_status().value,
            "alerts": len(self.alerts),
        }
