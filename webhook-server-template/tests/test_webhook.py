import sys, os, json
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from webhook import SignatureVerifier, WebhookProcessor, WebhookEvent


def test_signature_verify_valid():
    payload = b'{"event": "test"}'
    secret = "my_secret"
    sig = SignatureVerifier.sign(payload, secret)
    assert SignatureVerifier.verify(payload, sig, secret)


def test_signature_verify_invalid():
    payload = b'{"event": "test"}'
    assert not SignatureVerifier.verify(payload, "wrong_sig", "my_secret")


def test_signature_empty_secret():
    verifier = SignatureVerifier()
    sig = verifier.sign(b"data", "secret")
    assert len(sig) == 64  # SHA256 hex


def test_processor_no_secret():
    proc = WebhookProcessor()
    event = proc.process("order.created", {"id": 123})
    assert event.signature_valid is True


def test_processor_with_handler():
    proc = WebhookProcessor(max_retries=2, retry_delay=0.01)
    results = []

    @proc.on("order.created")
    def handle_order(payload):
        results.append(payload["id"])

    event = proc.process("order.created", {"id": 42})
    assert event.processed is True
    assert results == [42]


def test_processor_no_handler():
    proc = WebhookProcessor()
    event = proc.process("unknown.event", {"data": 1})
    assert event.processed is False
    assert "No handler" in event.error


def test_processor_retry():
    proc = WebhookProcessor(max_retries=3, retry_delay=0.01)
    attempts = []

    @proc.on("flaky.event")
    def flaky_handler(payload):
        attempts.append(1)
        if len(attempts) < 3:
            raise Exception("Temporary failure")
        # Succeed on 3rd attempt

    event = proc.process("flaky.event", {"x": 1})
    assert event.processed is True
    assert len(attempts) == 3


def test_processor_handler_always_fails():
    proc = WebhookProcessor(max_retries=2, retry_delay=0.01)

    @proc.on("bad.event")
    def bad_handler(payload):
        raise Exception("Permanent failure")

    event = proc.process("bad.event", {"x": 1})
    assert event.processed is False
    assert "Permanent failure" in event.error


def test_processor_stats():
    proc = WebhookProcessor()

    @proc.on("evt")
    def handler(payload):
        pass

    proc.process("evt", {"a": 1})
    proc.process("unknown", {"b": 2})
    stats = proc.stats()
    assert stats["total_events"] == 2
    assert stats["processed"] == 1
    assert stats["failed"] == 1


def test_processor_enqueue():
    proc = WebhookProcessor()
    proc.start_worker()

    @proc.on("async.event")
    def handler(payload):
        pass

    proc.enqueue("async.event", {"x": 1})
    import time
    time.sleep(0.5)
    stats = proc.stats()
    assert stats["total_events"] >= 1


def test_multiple_handlers():
    proc = WebhookProcessor()

    @proc.on("multi")
    def h1(payload):
        pass

    @proc.on("multi")
    def h2(payload):
        pass

    event = proc.process("multi", {"x": 1})
    assert event.processed is True
    assert proc.stats()["registered_handlers"]["multi"] == 2
