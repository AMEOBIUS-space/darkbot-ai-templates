# Notification Hub

> Multi-channel notifications: Telegram, Discord, Slack, Email, Webhook, Log

## Features

- 6 channel types: Telegram, Discord, Slack, Email, Webhook, Log
- Template engine with {{variable}} substitution
- Routing rules (priority-based channel selection)
- Broadcast to all enabled channels
- Rate limiting per channel
- Channel enable/disable
- Metadata support
- Statistics dashboard

## Quick Start

```python
from notifications import NotificationHub, ChannelType

hub = NotificationHub()
hub.register_channel("tg", ChannelType.TELEGRAM, {"bot_token": "...", "chat_id": "..."})
hub.register_channel("log", ChannelType.LOG)

hub.add_template("alert", "Alert: {{service}}", "{{service}} is {{status}}")
hub.send_templated("alert", {"service": "API", "status": "down"}, "log")
```

## Tests

```bash
python -m pytest tests/ -v
```

## License

MIT
