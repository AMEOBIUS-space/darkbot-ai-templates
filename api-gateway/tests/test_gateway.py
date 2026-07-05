import sys, os, time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from gateway import (APIGateway, LoadBalancer, LoadBalanceStrategy,
                     RateLimiter, Route, UpstreamService)


def test_load_balancer_round_robin():
    lb = LoadBalancer(LoadBalanceStrategy.ROUND_ROBIN)
    services = [UpstreamService("s", "http://a"), UpstreamService("s", "http://b")]
    first = lb.select(services)
    second = lb.select(services)
    assert first.url != second.url

def test_load_balancer_least_connections():
    lb = LoadBalancer(LoadBalanceStrategy.LEAST_CONNECTIONS)
    s1 = UpstreamService("s", "http://a", connections=5)
    s2 = UpstreamService("s", "http://b", connections=1)
    selected = lb.select([s1, s2])
    assert selected.url == "http://b"

def test_load_balancer_unhealthy():
    lb = LoadBalancer()
    s1 = UpstreamService("s", "http://a", healthy=False)
    s2 = UpstreamService("s", "http://b")
    selected = lb.select([s1, s2])
    assert selected.url == "http://b"

def test_load_balancer_no_healthy():
    lb = LoadBalancer()
    services = [UpstreamService("s", "http://a", healthy=False)]
    assert lb.select(services) is None

def test_rate_limiter_allow():
    rl = RateLimiter(default_limit=5)
    for _ in range(5):
        allowed, remaining = rl.check("client1")
        assert allowed is True
    allowed, remaining = rl.check("client1")
    assert allowed is False

def test_rate_limiter_per_client():
    rl = RateLimiter(default_limit=2)
    rl.check("c1")
    rl.check("c1")
    allowed, _ = rl.check("c1")
    assert not allowed
    allowed, _ = rl.check("c2")
    assert allowed

def test_add_upstream():
    gw = APIGateway()
    gw.add_upstream("api", "http://api1.example.com")
    gw.add_upstream("api", "http://api2.example.com")
    assert len(gw.upstreams["api"]) == 2

def test_add_route():
    gw = APIGateway()
    gw.add_route("/api/users", ["GET", "POST"], "api")
    assert "/api/users" in gw.routes

def test_match_route_exact():
    gw = APIGateway()
    gw.add_route("/api/users", ["GET"], "api")
    route = gw.match_route("/api/users", "GET")
    assert route is not None

def test_match_route_wildcard():
    gw = APIGateway()
    gw.add_route("/api/*", ["GET"], "api")
    route = gw.match_route("/api/anything", "GET")
    assert route is not None

def test_match_route_not_found():
    gw = APIGateway()
    gw.add_route("/api/users", ["GET"], "api")
    assert gw.match_route("/api/posts", "GET") is None

def test_match_route_wrong_method():
    gw = APIGateway()
    gw.add_route("/api/users", ["GET"], "api")
    assert gw.match_route("/api/users", "DELETE") is None

def test_process_request_success():
    gw = APIGateway()
    gw.add_upstream("api", "http://api1.example.com")
    gw.add_route("/api/users", ["GET"], "api")
    result = gw.process_request("GET", "/api/users", "client1")
    assert result["status"] == 200
    assert result["upstream"] == "http://api1.example.com"

def test_process_request_not_found():
    gw = APIGateway()
    result = gw.process_request("GET", "/nonexistent", "client1")
    assert result["status"] == 404

def test_process_request_auth_required():
    gw = APIGateway()
    gw.add_upstream("api", "http://api1.example.com")
    gw.add_route("/admin", ["GET"], "api", auth_required=True)
    gw.set_auth_verifier(lambda token: token == "valid")
    result = gw.process_request("GET", "/admin", "c1", auth_token="invalid")
    assert result["status"] == 401

def test_process_request_auth_success():
    gw = APIGateway()
    gw.add_upstream("api", "http://api1.example.com")
    gw.add_route("/admin", ["GET"], "api", auth_required=True)
    gw.set_auth_verifier(lambda token: token == "valid")
    result = gw.process_request("GET", "/admin", "c1", auth_token="valid")
    assert result["status"] == 200

def test_process_request_rate_limited():
    gw = APIGateway()
    gw.add_upstream("api", "http://api1.example.com")
    gw.add_route("/api", ["GET"], "api", rate_limit=2)
    gw.process_request("GET", "/api", "c1")
    gw.process_request("GET", "/api", "c1")
    result = gw.process_request("GET", "/api", "c1")
    assert result["status"] == 429

def test_process_request_no_healthy():
    gw = APIGateway()
    gw.add_upstream("api", "http://api1.example.com")
    gw.mark_unhealthy("api", "http://api1.example.com")
    gw.add_route("/api", ["GET"], "api")
    result = gw.process_request("GET", "/api", "c1")
    assert result["status"] == 503

def test_mark_healthy():
    gw = APIGateway()
    gw.add_upstream("api", "http://api1.example.com")
    gw.mark_unhealthy("api", "http://api1.example.com")
    assert not gw.upstreams["api"][0].healthy
    gw.mark_healthy("api", "http://api1.example.com")
    assert gw.upstreams["api"][0].healthy

def test_stats():
    gw = APIGateway()
    gw.add_upstream("api", "http://a.com")
    gw.add_upstream("api", "http://b.com")
    gw.add_route("/api", ["GET"], "api")
    gw.process_request("GET", "/api", "c1")
    stats = gw.stats()
    assert stats["routes"] == 1
    assert stats["upstreams"] == 1
    assert stats["total_services"] == 2
    assert stats["requests_logged"] == 1
