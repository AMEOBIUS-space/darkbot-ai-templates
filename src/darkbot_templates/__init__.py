"""DarkBot AI — Production-ready Python code templates.

20 templates: TG bots, scrapers, AI agents, crypto trading, Tor, JWT auth.
Zero dependencies. Pure Python stdlib.
"""
__version__ = "1.7.8"
__all__ = ["templates", "CircuitBreaker", "BackpressureHandler", "ServiceRegistry", "HealthChecker"]

from .templates.circuit_breaker import CircuitBreaker
from .templates.backpressure_handler import BackpressureHandler
from .templates.service_registry import ServiceRegistry
from .templates.health_checker import HealthChecker
