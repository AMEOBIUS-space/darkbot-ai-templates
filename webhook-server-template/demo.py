#!/usr/bin/env python3
"""Demo: Webhook Server Template."""
import sys, os, json
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))
from webhook import WebhookProcessor, SignatureVerifier

proc = WebhookProcessor(secret="my_webhook_secret", max_retries=3, retry_delay=0.1)

@proc.on("order.created")
def handle_order(payload):
    print(f"  Order created: #{payload['order_id']} - ${payload['amount']}")

@proc.on("payment.received")
def handle_payment(payload):
    print(f"  Payment received: ${payload['amount']} from {payload['email']}")

# Simulate webhook
payload = {"order_id": 42, "amount": 99.99}
raw = json.dumps(payload).encode()
sig = SignatureVerifier.sign(raw, "my_webhook_secret")

print("=== Valid Webhook ===")
event = proc.process("order.created", payload, signature=sig, raw_payload=raw)
print(f"  Processed: {event.processed}, Valid: {event.signature_valid}")

print("\n=== Invalid Signature ===")
event = proc.process("order.created", payload, signature="wrong", raw_payload=raw)
print(f"  Processed: {event.processed}, Error: {event.error}")

print("\n=== Unknown Event ===")
event = proc.process("unknown.event", {"x": 1})
print(f"  Processed: {event.processed}, Error: {event.error}")

print(f"\nStats: {json.dumps(proc.stats(), indent=2)}")
