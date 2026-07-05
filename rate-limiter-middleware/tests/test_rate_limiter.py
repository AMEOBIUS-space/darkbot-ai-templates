import sys, os, time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from rate_limiter import TokenBucket, SlidingWindow, RateLimiterMiddleware


def test_token_bucket_consume():
    bucket = TokenBucket(capacity=5, refill_rate=10.0)
    for _ in range(5):
        assert bucket.consume(1)
    assert not bucket.consume(1)


def test_token_bucket_refill():
    bucket = TokenBucket(capacity=2, refill_rate=100.0)
    bucket.consume(2)
    assert not bucket.consume(1)
    time.sleep(0.05)
    assert bucket.consume(1)


def test_token_bucket_retry_after():
    bucket = TokenBucket(capacity=1, refill_rate=10.0)
    bucket.consume(1)
    retry = bucket.retry_after(1)
    assert retry > 0
    assert retry < 1.0


def test_sliding_window_check():
    window = SlidingWindow(window_seconds=1, max_requests=3)
    assert window.check()
    assert window.check()
    assert window.check()
    assert not window.check()


def test_sliding_window_reset():
    window = SlidingWindow(window_seconds=0.1, max_requests=2)
    assert window.check()
    assert window.check()
    time.sleep(0.15)
    assert window.check()


def test_middleware_default():
    rl = RateLimiterMiddleware(strategy="token_bucket", default_limit=5, refill_rate=100.0)
    for _ in range(5):
        allowed, _, _ = rl.check("user1")
        assert allowed
    allowed, _, _ = rl.check("user1")
    assert not allowed


def test_middleware_custom_limit():
    rl = RateLimiterMiddleware(default_limit=100)
    rl.set_limit("premium_user", 10, 60)
    limiter = rl._get_limiter("premium_user")
    assert limiter.capacity == 10


def test_middleware_headers():
    rl = RateLimiterMiddleware(default_limit=5, refill_rate=100.0)
    allowed, retry, headers = rl.check("user1")
    assert "X-RateLimit-Limit" in headers
    assert "X-RateLimit-Remaining" in headers
    assert headers["X-RateLimit-Limit"] == "5"


def test_middleware_429():
    rl = RateLimiterMiddleware(default_limit=1, refill_rate=0.1)
    rl.check("user1")
    allowed, retry, headers = rl.check("user1")
    assert not allowed
    assert retry > 0


def test_middleware_stats():
    rl = RateLimiterMiddleware(default_limit=10)
    rl.check("user1")
    rl.check("user2")
    rl.set_limit("vip", 1000)
    stats = rl.stats()
    assert stats["tracked_keys"] == 2
    assert stats["custom_limits"] == 1


def test_middleware_per_key_isolation():
    rl = RateLimiterMiddleware(default_limit=2, refill_rate=0.1)
    rl.check("user1")
    rl.check("user1")
    allowed2, _, _ = rl.check("user2")
    assert allowed2
    allowed1, _, _ = rl.check("user1")
    assert not allowed1
