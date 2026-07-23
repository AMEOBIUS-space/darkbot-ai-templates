# Webhook Server: Receive and Verify Without Flask

> Part of the [darkbot-templates](https://github.com/AMEOBIUS-space/darkbot-ai-templates) series — zero-dependency production templates.

Webhooks are how APIs tell you something happened — payment received, repo pushed, build finished. This template receives webhooks, verifies signatures, and routes events to handlers — all with stdlib `http.server`.

## Usage

```python
from darkbot_templates.templates.webhook_server import WebhookRouter

router = WebhookRouter(secret="your-webhook-secret")

# Register event handlers
@router.on("payment.succeeded")
def handle_payment(payload):
    amount = payload["amount"]
    user = payload["customer"]
    print(f"Payment received: ${amount} from {user}")
    return {"status": "ok"}

@router.on("payment.failed")
def handle_failure(payload):
    notify_admin(payload["reason"])
    return {"status": "alerted"}

# Handle unknown events
@router.default
def handle_unknown(payload):
    print(f"Unknown event: {payload}")
    return {"status": "ignored"}
```

## Signature Verification

```python
router = WebhookRouter(secret="whsec_xxx")

# Verifies HMAC-SHA256 signature
# Supports GitHub (X-Hub-Signature-256) and Stripe (Stripe-Signature) conventions
payload = b'{"event": "payment.succeeded", "amount": 500}'
signature = "sha256=a1b2c3d4..."

is_valid = router.verify_signature(payload, signature)
if not is_valid:
    raise ValueError("Invalid signature — possible forgery")
```

## Dispatching Events

```python
# In your HTTP handler:
event_type = headers.get("X-Event-Type", "unknown")
payload = json.loads(body)

result = router.dispatch(event_type, payload)
# → {"status": "ok"}  (from your handler)
```

## Running as HTTP Server

```python
from http.server import HTTPServer

router = WebhookRouter(secret="whsec_xxx")

@router.on("push")
def on_push(payload):
    repo = payload["repository"]["name"]
    print(f"Push to {repo}")
    return {"status": "processed"}

# Start built-in server on port 8080
server = router.serve(host="0.0.0.0", port=8080)
# POST to http://localhost:8080/webhook
```

## GitHub Webhooks

```python
router = WebhookRouter(secret=os.environ["GITHUB_WEBHOOK_SECRET"])

@router.on("push")
def on_push(payload):
    for commit in payload["commits"]:
        print(f"  {commit['id'][:7]} {commit['message']}")

@router.on("pull_request")
def on_pr(payload):
    action = payload["action"]
    pr = payload["pull_request"]
    if action == "opened":
        print(f"New PR: {pr['title']}")

@router.on("issues")
def on_issue(payload):
    action = payload["action"]
    issue = payload["issue"]
    print(f"Issue {action}: #{issue['number']} {issue['title']}")
```

## Stripe Webhooks

```python
router = WebhookRouter(secret=os.environ["STRIPE_WEBHOOK_SECRET"])

@router.on("checkout.session.completed")
def handle_checkout(payload):
    session = payload["data"]["object"]
    customer_email = session["customer_details"]["email"]
    amount = session["amount_total"] / 100
    print(f"Payment: {customer_email} paid ${amount:.2f}")
    fulfill_order(session)

@router.on("invoice.payment_failed")
def handle_failure(payload):
    invoice = payload["data"]["object"]
    notify_customer(invoice["customer_email"], "Payment failed")
```

## Freelance Platform Notifications

```python
router = WebhookRouter()

@router.on("bid.accepted")
def on_accepted(payload):
    platform = payload["platform"]
    job_id = payload["job_id"]
    amount = payload["amount"]
    send_email(f"Bid accepted on {platform}! Job #{job_id}, ${amount}")

@router.on("message.received")
def on_message(payload):
    platform = payload["platform"]
    sender = payload["sender"]
    text = payload["text"]
    log_message(platform, sender, text)

router.serve(host="0.0.0.0", port=9090)
```

## Error Handling

The `dispatch` method catches exceptions from handlers and returns an error response instead of crashing:

```python
result = router.dispatch("payment.succeeded", payload)
# If handler raises: {"status": "error", "error": "Connection refused"}
# If no handler: {"status": "ignored", "reason": "No handler for 'unknown.event'"}
# If success: whatever your handler returns
```

## Testing

```bash
pytest tests/test_templates.py -k webhook -v
```

## References

- [GitHub Webhooks](https://docs.github.com/en/webhooks)
- [Stripe Webhooks](https://stripe.com/docs/webhooks)
- [HMAC Signature Verification](https://docs.github.com/en/webhooks/verifying-webhooks)

---

*darkbot-templates v1.8.5 — 30 templates, zero dependencies, 448 tests.*
