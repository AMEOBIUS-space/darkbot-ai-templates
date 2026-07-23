# Pub/Sub Broker: In-Process Event Bus

> Part of the [darkbot-templates](https://github.com/AMEOBIUS-space/darkbot-ai-templates) series — zero-dependency production templates.

When components need to talk to each other without tight coupling, the pub/sub pattern is the answer. This template gives you an in-process event bus with wildcard topic matching — no Redis, no RabbitMQ, just Python.

## Usage

```python
from darkbot_templates.templates.pubsub_broker import PubSubBroker

bus = PubSubBroker()

# Subscribe
def on_order(data):
    print(f"Order received: {data}")

bus.subscribe("orders.*", on_order)

# Publish
bus.publish("orders.created", {"id": 42, "total": 99.95})
bus.publish("orders.cancelled", {"id": 42})
# Both match "orders.*" pattern
```

## Wildcard Topics

Topics use `fnmatch` patterns — `*` matches anything:

```python
bus.subscribe("user.*", user_handler)        # user.created, user.deleted, user.updated
bus.subscribe("*.error", error_handler)      # payment.error, auth.error, db.error
bus.subscribe("payment.*.failed", fail_handler)  # payment.eu.failed, payment.us.failed
bus.subscribe("*", catch_all)                 # everything
```

## Priority Subscribers

Higher priority subscribers receive events first:

```python
bus.subscribe("order.*", audit_log, priority=10)   # runs first
bus.subscribe("order.*", process_order, priority=5) # runs second
bus.subscribe("order.*", send_email, priority=1)    # runs last
```

## Event History

```python
bus = PubSubBroker(history_size=1000)

# ... publish events ...

for evt in bus.history:
    print(f"  {evt.timestamp:.0f}  {evt.topic}  → {evt.data}")
```

## Telegram Bot Integration

```python
bus = PubSubBroker()

# Wire bot events into the bus
async def handle_update(update):
    topic = f"tg.{update.message.chat.type}.{update.message.text.split('/')[0]}"
    bus.publish(topic, update.to_dict())

# Multiple handlers, decoupled
bus.subscribe("tg.private.*", private_chat_handler)
bus.subscribe("tg.group.*", group_chat_handler)
bus.subscribe("tg.*.help", help_command_handler)
bus.subscribe("*", metrics_recorder, priority=0)
```

## Thread Safety

All operations acquire a `threading.Lock`. Safe to publish and subscribe from different threads concurrently.

## Testing

```bash
pytest tests/test_pubsub_broker.py -v
```

## References

- [Redis Pub/Sub](https://redis.io/topics/pubsub) — the pattern this template mimics
- [Event-Driven Architecture](https://microservices.io/patterns/data/event-driven-architecture.html)

---

*darkbot-templates v1.8.5 — 30 templates, zero dependencies, 448 tests.*
