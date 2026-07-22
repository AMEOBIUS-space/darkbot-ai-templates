# Webhook Server Template

> Receive, verify, and process webhooks with HMAC-SHA256 signatures and retry logic

## Features

- HMAC-SHA256 signature verification (sign + verify)
- Handler registry with decorator pattern
- Retry logic with exponential backoff
- Async processing via background worker + queue
- Multiple handlers per event type
- Statistics tracking (total, processed, failed, invalid signatures)

## Quick Start

```python
from webhook import WebhookProcessor

proc = WebhookProcessor(secret="your_secret", max_retries=3)

@proc.on("order.created")
def handle_order(payload):
    print(f"New order: {payload['order_id']}")

event = proc.process("order.created", {"order_id": 42}, signature=sig, raw_payload=raw)
```

## Tests

```bash
python -m pytest tests/ -v
```

## License

MIT

Freelance portfolio: [https://ameobius-space.github.io/kwork-portfolio/](https://ameobius-space.github.io/kwork-portfolio/)
