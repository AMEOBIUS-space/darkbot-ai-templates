"""API Gateway — routing, load balancing, rate limiting, and auth middleware."""
import time
import hashlib
import threading
from typing import Dict, List, Optional, Callable, Any, Tuple
from dataclasses import dataclass, asdict, field
from datetime import datetime
from enum import Enum
from collections import defaultdict, deque


class LoadBalanceStrategy(Enum):
    ROUND_ROBIN = "round_robin"
    RANDOM = "random"
    LEAST_CONNECTIONS = "least_connections"
    WEIGHTED = "weighted"


@dataclass
class UpstreamService:
    name: str
    url: str
    weight: int = 1
    healthy: bool = True
    connections: int = 0
    last_health_check: str = ""


@dataclass
class Route:
    path: str
    methods: List[str]
    upstream: str
    strip_prefix: bool = False
    rate_limit: int = 0  # requests per minute, 0 = no limit
    auth_required: bool = False
    timeout: int = 30
    cors_enabled: bool = True


@dataclass
class RequestLog:
    method: str
    path: str
    upstream: str
    status: int
    duration: float
    timestamp: str
    client_ip: str = ""


class LoadBalancer:
    """Load balancer with multiple strategies."""

    def __init__(self, strategy: LoadBalanceStrategy = LoadBalanceStrategy.ROUND_ROBIN):
        self.strategy = strategy
        self._index = 0
        self._lock = threading.Lock()

    def select(self, services: List[UpstreamService]) -> Optional[UpstreamService]:
        healthy = [s for s in services if s.healthy]
        if not healthy:
            return None

        with self._lock:
            if self.strategy == LoadBalanceStrategy.ROUND_ROBIN:
                service = healthy[self._index % len(healthy)]
                self._index += 1
                return service

            elif self.strategy == LoadBalanceStrategy.RANDOM:
                import random
                return random.choice(healthy)

            elif self.strategy == LoadBalanceStrategy.LEAST_CONNECTIONS:
                return min(healthy, key=lambda s: s.connections)

            elif self.strategy == LoadBalanceStrategy.WEIGHTED:
                total_weight = sum(s.weight for s in healthy)
                if total_weight == 0:
                    return healthy[0]
                import random
                r = random.randint(1, total_weight)
                cumulative = 0
                for s in healthy:
                    cumulative += s.weight
                    if r <= cumulative:
                        return s
                return healthy[-1]

        return healthy[0]


class RateLimiter:
    """Per-client rate limiter for the gateway."""

    def __init__(self, default_limit: int = 100):
        self.default_limit = default_limit
        self._buckets: Dict[str, deque] = defaultdict(deque)
        self._lock = threading.Lock()

    def check(self, client_id: str, limit: int = None) -> Tuple[bool, int]:
        """Check if request is allowed. Returns (allowed, remaining)."""
        max_requests = limit or self.default_limit
        now = time.time()
        window = 60.0  # 1 minute

        with self._lock:
            bucket = self._buckets[client_id]
            while bucket and bucket[0] < now - window:
                bucket.popleft()

            if len(bucket) >= max_requests:
                return False, 0

            bucket.append(now)
            return True, max_requests - len(bucket)


class APIGateway:
    """API Gateway with routing, load balancing, rate limiting, and auth."""

    def __init__(self, lb_strategy: LoadBalanceStrategy = LoadBalanceStrategy.ROUND_ROBIN,
                 default_rate_limit: int = 100):
        self.routes: Dict[str, Route] = {}
        self.upstreams: Dict[str, List[UpstreamService]] = {}
        self.load_balancer = LoadBalancer(lb_strategy)
        self.rate_limiter = RateLimiter(default_rate_limit)
        self.auth_verifier: Optional[Callable] = None
        self.request_log: List[RequestLog] = []
        self._max_log = 1000
        self._lock = threading.Lock()

    def add_upstream(self, name: str, url: str, weight: int = 1):
        if name not in self.upstreams:
            self.upstreams[name] = []
        self.upstreams[name].append(UpstreamService(name=name, url=url, weight=weight))

    def add_route(self, path: str, methods: List[str], upstream: str,
                  rate_limit: int = 0, auth_required: bool = False, **kwargs):
        route = Route(path=path, methods=methods, upstream=upstream,
                      rate_limit=rate_limit, auth_required=auth_required, **kwargs)
        self.routes[path] = route

    def set_auth_verifier(self, verifier: Callable):
        self.auth_verifier = verifier

    def match_route(self, path: str, method: str) -> Optional[Route]:
        """Find matching route for a request."""
        for route_path, route in self.routes.items():
            if self._path_matches(route_path, path) and method in route.methods:
                return route
        return None

    @staticmethod
    def _path_matches(pattern: str, path: str) -> bool:
        if pattern == path:
            return True
        if pattern.endswith("/*"):
            prefix = pattern[:-2]
            return path.startswith(prefix)
        if pattern.endswith("/{id}"):
            prefix = pattern[:-5]
            return path.startswith(prefix + "/") and len(path) > len(prefix) + 1
        return False

    def select_upstream(self, upstream_name: str) -> Optional[UpstreamService]:
        services = self.upstreams.get(upstream_name, [])
        return self.load_balancer.select(services)

    def process_request(self, method: str, path: str, client_id: str = "",
                        auth_token: str = None) -> Dict:
        """Process a request through the gateway."""
        start = time.time()
        result = {"status": 200, "upstream": "", "error": ""}

        # Match route
        route = self.match_route(path, method)
        if not route:
            result["status"] = 404
            result["error"] = "Route not found"
            self._log(method, path, "", 404, time.time() - start, client_id)
            return result

        # Auth check
        if route.auth_required:
            if not self.auth_verifier or not self.auth_verifier(auth_token):
                result["status"] = 401
                result["error"] = "Unauthorized"
                self._log(method, path, route.upstream, 401, time.time() - start, client_id)
                return result

        # Rate limit check
        if route.rate_limit > 0:
            allowed, remaining = self.rate_limiter.check(client_id, route.rate_limit)
            if not allowed:
                result["status"] = 429
                result["error"] = "Rate limited"
                self._log(method, path, route.upstream, 429, time.time() - start, client_id)
                return result

        # Select upstream
        service = self.select_upstream(route.upstream)
        if not service:
            result["status"] = 503
            result["error"] = "No healthy upstream"
            self._log(method, path, route.upstream, 503, time.time() - start, client_id)
            return result

        result["upstream"] = service.url
        result["status"] = 200
        self._log(method, path, route.upstream, 200, time.time() - start, client_id)
        return result

    def _log(self, method: str, path: str, upstream: str, status: int,
             duration: float, client_ip: str):
        with self._lock:
            self.request_log.append(RequestLog(
                method=method, path=path, upstream=upstream, status=status,
                duration=duration, timestamp=datetime.now().isoformat(),
                client_ip=client_ip,
            ))
            if len(self.request_log) > self._max_log:
                self.request_log = self.request_log[-self._max_log:]

    def mark_unhealthy(self, upstream_name: str, url: str):
        for s in self.upstreams.get(upstream_name, []):
            if s.url == url:
                s.healthy = False
                s.last_health_check = datetime.now().isoformat()

    def mark_healthy(self, upstream_name: str, url: str):
        for s in self.upstreams.get(upstream_name, []):
            if s.url == url:
                s.healthy = True
                s.last_health_check = datetime.now().isoformat()

    def stats(self) -> Dict:
        return {
            "routes": len(self.routes),
            "upstreams": len(self.upstreams),
            "total_services": sum(len(s) for s in self.upstreams.values()),
            "healthy_services": sum(1 for services in self.upstreams.values()
                                    for s in services if s.healthy),
            "requests_logged": len(self.request_log),
            "lb_strategy": self.load_balancer.strategy.value,
        }
