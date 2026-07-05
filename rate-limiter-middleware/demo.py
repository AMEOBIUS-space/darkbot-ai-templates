#!/usr/bin/env python3
"""Demo: API Rate Limiter Middleware."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))
from rate_limiter import RateLimiterMiddleware

rl = RateLimiterMiddleware(strategy="token_bucket", default_limit=5, refill_rate=2.0)
rl.set_limit("premium_user", 1000)

print("=== Rate Limiter Demo ===\n")
for user in ["user1", "user1", "user1", "user1", "user1", "user1"]:
    allowed, retry, headers = rl.check(user)
    status = "ALLOWED" if allowed else f"BLOCKED (retry in {retry:.1f}s)"
    print(f"  {user}: {status} | Remaining: {headers['X-RateLimit-Remaining']}")

print("\n  premium_user: first request")
allowed, _, headers = rl.check("premium_user")
print(f"  premium_user: {'ALLOWED' if allowed else 'BLOCKED'} | Remaining: {headers['X-RateLimit-Remaining']}")

print(f"\nStats: {rl.stats()}")
