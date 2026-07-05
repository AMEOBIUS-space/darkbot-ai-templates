#!/usr/bin/env python3
"""Demo: Health Check Monitor."""
import sys, os, json, time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))
from health import HealthMonitor, ServiceStatus, CircuitState

mon = HealthMonitor()

# Register alert handler
alerts = []
mon.add_alert_handler(lambda a: alerts.append(a))

# Add checks
mon.add_check("api", "https://httpbin.org/status/200", timeout=5)
mon.add_check("db", "https://nonexistent.invalid", timeout=2, failure_threshold=2, recovery_timeout=5)
mon.add_check("cache", "https://httpbin.org/status/200", timeout=5)

# Check services
print("=== Checking Services ===")
for name in mon.checks:
    check = mon.check_service(name)
    print(f"  {name}: {check.last_status.value} | {check.last_response_time:.2f}s | failures={check.consecutive_failures}")

# Circuit breaker for DB
print(f"\n=== DB Circuit Breaker ===")
db_circuit = mon.circuits["db"]
print(f"  State: {db_circuit.state.value}")
print(f"  Stats: {json.dumps(db_circuit.stats(), indent=2)}")

# Overall status
print(f"\n=== Overall Status ===")
print(f"  {mon.overall_status().value}")

# Alerts
print(f"\n=== Alerts ({len(alerts)}) ===")
for a in alerts:
    print(f"  [{a['service']}] {a['type']}: {a['message'][:60]}")

# Stats
print(f"\n=== Stats ===")
print(json.dumps(mon.stats(), indent=2))
