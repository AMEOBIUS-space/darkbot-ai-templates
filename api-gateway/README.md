# API Gateway

> Routing, load balancing, rate limiting, and auth middleware

## Features

- **LoadBalancer** — 4 strategies: round_robin, random, least_connections, weighted
- **RateLimiter** — per-client rate limiting with configurable limits per route
- **Route matching** — exact, wildcard (/*), parameterized (/{id})
- **Auth middleware** — configurable auth verifier
- **Health checking** — mark upstreams healthy/unhealthy
- **Request logging** — all requests logged with status, duration, upstream
- **Statistics** — routes, upstreams, services, health, strategy

## Quick Start

```python
from gateway import APIGateway, LoadBalanceStrategy

gw = APIGateway(lb_strategy=LoadBalanceStrategy.LEAST_CONNECTIONS)
gw.add_upstream("api", "http://api1.example.com")
gw.add_upstream("api", "http://api2.example.com")
gw.add_route("/api/*", ["GET", "POST"], "api", rate_limit=100, auth_required=True)
gw.set_auth_verifier(lambda token: verify_jwt(token))

result = gw.process_request("GET", "/api/users", "client1", auth_token="jwt...")
```

## Tests

```bash
python -m pytest tests/ -v
```

## License

MIT

Freelance portfolio: [https://ameobius-space.github.io/kwork-portfolio/](https://ameobius-space.github.io/kwork-portfolio/)
