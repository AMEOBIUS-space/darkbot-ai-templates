# Email Campaign Automation

> Template rendering, subscriber management, SMTP sending, and open/click tracking

## Features

- Template engine with {{variable}} substitution + auto-extraction
- Subscriber list with tags, unsubscribe, metadata
- Campaign creation with scheduling
- SMTP sending (TLS)
- Open tracking via pixel
- Click tracking
- Campaign statistics (sent, failed, opened, clicked, unsubscribed)

## Quick Start

```python
from campaign import EmailCampaignManager, EmailTemplate

mgr = EmailCampaignManager(smtp_host="smtp.gmail.com", smtp_port=587,
                           smtp_user="you@gmail.com", smtp_pass="app_password",
                           from_email="you@gmail.com")

mgr.add_template(EmailTemplate("welcome", "Hi {{name}}", "<p>Welcome {{name}}!</p>"))
lst = mgr.create_list("subscribers")
lst.add("user@example.com", "User")
mgr.create_campaign("c1", "Welcome", "welcome", "subscribers")
mgr.send_campaign("c1", {"name": "User"})
```

## Tests

```bash
python -m pytest tests/ -v
```

## License

MIT
