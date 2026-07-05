# Event Bus

> Pub/sub event system with priorities, middleware, and async support

## Features

- **EventBus** (sync): subscribe, publish, priority ordering, middleware, wildcard
- **AsyncEventBus**: async/await handlers with sync fallback
- Priority-based handler execution (higher = first)
- Middleware (can modify or block events)
- Wildcard subscriptions (receive all events)
- Event history with filtering
- Handler error isolation (one failing handler doesn't stop others)
- Unsubscribe support
- Statistics

## Quick Start

```python
from bus import EventBus

bus = EventBus()
bus.subscribe("user.created", lambda e: send_welcome(e.data), priority=10)
bus.subscribe("user.created", lambda e: log_event(e.data), priority=1)
bus.use(lambda e: audit_log(e))  # Middleware
bus.publish("user.created", {"name": "Alice", "email": "alice@example.com"})
```

## Tests

```bash
python -m pytest tests/ -v
```

## License

MIT
