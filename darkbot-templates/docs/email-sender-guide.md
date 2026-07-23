# Email Sender: SMTP Without Extra Libraries

> Part of the [darkbot-templates](https://github.com/AMEOBIUS-space/darkbot-ai-templates) series — zero-dependency production templates.

Sending email shouldn't require a third-party service SDK. This template wraps Python's `smtplib` with templates, attachments, retry, and multi-recipient support — pure stdlib.

## Usage

```python
from darkbot_templates.templates.email_sender import EmailSender

sender = EmailSender(
    host="smtp.gmail.com",
    port=587,
    username="you@gmail.com",
    password="app-password",  # Gmail app password, not account password
    use_tls=True,
)

# Simple send
sender.send(
    to="client@example.com",
    subject="Your order has shipped",
    body="Your order #42 is on its way!",
)

# HTML email
sender.send(
    to="client@example.com",
    subject="Invoice #1234",
    body="Plain text fallback",
    html="<h1>Invoice #1234</h1><p>Amount due: <b>$500</b></p>",
)
```

## Multiple Recipients

```python
sender.send(
    to=["alice@example.com", "bob@example.com"],
    cc=["manager@example.com"],
    bcc=["archive@example.com"],
    subject="Team update",
    body="Weekly status report attached.",
)
```

## Attachments

```python
sender.send(
    to="client@example.com",
    subject="Your report",
    body="Please find the report attached.",
    attachments=[
        "/path/to/report.pdf",
        "/path/to/data.csv",
    ],
)
```

## Template Strings

```python
template = """
Hello {name},

Your bid on {job_title} has been {status}.

Amount: {amount} {currency}

Best regards,
{sender_name}
"""

sender.send_template(
    to="client@example.com",
    subject="Bid status update",
    template=template,
    variables={
        "name": "Alice",
        "job_title": "Telegram Bot Development",
        "status": "accepted",
        "amount": "500",
        "currency": "USD",
        "sender_name": "DarkBot AI",
    },
)
```

## Retry on Failure

```python
sender = EmailSender(
    host="smtp.example.com",
    port=587,
    username="bot@example.com",
    password="secret",
    max_retries=3,        # retry up to 3 times
    retry_delay=5.0,      # wait 5s between retries
)

# Transient SMTP failures are retried automatically
sender.send(to="client@example.com", subject="Hello", body="World")
```

## Gmail Setup

```python
# 1. Enable 2FA on your Google account
# 2. Generate an App Password: https://myaccount.google.com/apppasswords
# 3. Use the 16-character app password:

sender = EmailSender(
    host="smtp.gmail.com",
    port=587,
    username="your@gmail.com",
    password="xxxx xxxx xxxx xxxx",  # app password
    use_tls=True,
)
```

## Freelance Notification Pipeline

```python
from darkbot_templates.templates.email_sender import EmailSender
from darkbot_templates.templates.sqlite_orm import Database

sender = EmailSender(
    host=os.environ["SMTP_HOST"],
    port=int(os.environ.get("SMTP_PORT", 587)),
    username=os.environ["SMTP_USER"],
    password=os.environ["SMTP_PASS"],
)

db = Database("freelance.db")

# Notify on accepted bids
accepted = db.table("bids").where("status", "=", "accepted").where("notified", "=", 0).all()

for bid in accepted:
    sender.send(
        to=os.environ["NOTIFY_EMAIL"],
        subject=f"Bid accepted: {bid['platform']} #{bid['job_id']}",
        body=f"Your bid of {bid['amount']} on {bid['platform']} was accepted!",
    )
    db.table("bids").where("id", "=", bid["id"]).update({"notified": 1})
```

## Bulk Send with Rate Limiting

```python
from darkbot_templates.templates.rate_limiter import TokenBucketRateLimiter

limiter = TokenBucketRateLimiter(rate=1.0, capacity=5)  # 1 email/second, burst 5

for recipient in mailing_list:
    while not limiter.allow("smtp"):
        time.sleep(limiter.wait_time("smtp"))
    sender.send(to=recipient, subject=subject, body=body)
```

## Testing

```bash
pytest tests/test_email_sender.py -v
```

## References

- [smtplib docs](https://docs.python.org/3/library/smtplib.html)
- [email.mime docs](https://docs.python.org/3/library/email.mime.html)
- [Gmail App Passwords](https://support.google.com/accounts/answer/185833)

---

*darkbot-templates v1.8.5 — 30 templates, zero dependencies, 448 tests.*
