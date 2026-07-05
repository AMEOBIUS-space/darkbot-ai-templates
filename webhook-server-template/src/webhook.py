"""Webhook Server Template — receive, verify, and process webhooks with retry."""
import hmac
import hashlib
import json
import time
import threading
from typing import Dict, List, Callable, Optional, Any
from dataclasses import dataclass, asdict
from datetime import datetime
from queue import Queue


@dataclass
class WebhookEvent:
    event_id: str
    event_type: str
    payload: Dict
    received_at: str
    signature_valid: bool
    processed: bool = False
    error: Optional[str] = None


class SignatureVerifier:
    """Verify webhook signatures (HMAC-SHA256)."""

    @staticmethod
    def verify(payload: bytes, signature: str, secret: str, algorithm: str = "sha256") -> bool:
        expected = hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()
        return hmac.compare_digest(expected, signature)

    @staticmethod
    def sign(payload: bytes, secret: str) -> str:
        return hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()


class WebhookProcessor:
    """Process webhooks with handler registry and async queue."""

    def __init__(self, secret: str = "", max_retries: int = 3, retry_delay: float = 1.0):
        self.secret = secret
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.handlers: Dict[str, List[Callable]] = {}
        self.events: List[WebhookEvent] = []
        self.queue: Queue = Queue()
        self._worker_thread = None

    def on(self, event_type: str):
        """Register handler for event type."""
        def decorator(func: Callable):
            if event_type not in self.handlers:
                self.handlers[event_type] = []
            self.handlers[event_type].append(func)
            return func
        return decorator

    def verify_signature(self, payload: bytes, signature: str) -> bool:
        if not self.secret:
            return True
        return SignatureVerifier.verify(payload, signature, self.secret)

    def process(self, event_type: str, payload: Dict, signature: str = "",
                raw_payload: bytes = b"") -> WebhookEvent:
        """Process a webhook event synchronously."""
        sig_valid = self.verify_signature(raw_payload or json.dumps(payload).encode(), signature)
        event = WebhookEvent(
            event_id=f"evt_{int(time.time() * 1000)}",
            event_type=event_type,
            payload=payload,
            received_at=datetime.now().isoformat(),
            signature_valid=sig_valid,
        )

        if not sig_valid:
            event.error = "Invalid signature"
            self.events.append(event)
            return event

        # Execute handlers with retry
        handlers = self.handlers.get(event_type, [])
        if not handlers:
            event.error = f"No handler for '{event_type}'"
            self.events.append(event)
            return event

        for handler in handlers:
            success = False
            for attempt in range(self.max_retries):
                try:
                    handler(payload)
                    success = True
                    break
                except Exception as e:
                    if attempt < self.max_retries - 1:
                        time.sleep(self.retry_delay * (attempt + 1))
                    else:
                        event.error = str(e)

        event.processed = success
        self.events.append(event)
        return event

    def start_worker(self):
        """Start background worker for async processing."""
        def worker():
            while True:
                item = self.queue.get()
                if item is None:
                    break
                event_type, payload, signature, raw = item
                self.process(event_type, payload, signature, raw)
                self.queue.task_done()

        self._worker_thread = threading.Thread(target=worker, daemon=True)
        self._worker_thread.start()

    def enqueue(self, event_type: str, payload: Dict, signature: str = "", raw_payload: bytes = b""):
        """Enqueue webhook for async processing."""
        self.queue.put((event_type, payload, signature, raw_payload))

    def stats(self) -> Dict:
        return {
            "total_events": len(self.events),
            "processed": sum(1 for e in self.events if e.processed),
            "failed": sum(1 for e in self.events if not e.processed),
            "invalid_signatures": sum(1 for e in self.events if not e.signature_valid),
            "registered_handlers": {k: len(v) for k, v in self.handlers.items()},
        }
