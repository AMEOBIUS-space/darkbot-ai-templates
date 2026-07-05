"""Email Campaign Automation — template rendering, list management, scheduling, tracking."""
import json
import time
import re
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict, field
from datetime import datetime
from collections import defaultdict


@dataclass
class Subscriber:
    email: str
    name: str = ""
    tags: List[str] = field(default_factory=list)
    subscribed_at: str = ""
    unsubscribed: bool = False
    metadata: Dict = field(default_factory=dict)


@dataclass
class EmailTemplate:
    name: str
    subject: str
    body_html: str
    body_text: str = ""
    variables: List[str] = field(default_factory=list)


@dataclass
class Campaign:
    id: str
    name: str
    template_name: str
    recipients: List[str] = field(default_factory=list)
    sent: int = 0
    failed: int = 0
    opened: int = 0
    clicked: int = 0
    unsubscribed: int = 0
    scheduled_at: str = ""
    sent_at: str = ""


class TemplateEngine:
    """Render email templates with variable substitution."""

    @staticmethod
    def render(template: str, variables: Dict) -> str:
        result = template
        for key, value in variables.items():
            result = result.replace(f"{{{{{key}}}}}", str(value))
            result = result.replace(f"{{{{ {key} }}}}", str(value))
        return result

    @staticmethod
    def extract_variables(template: str) -> List[str]:
        return list(set(re.findall(r"\{\{(\w+)\}\}", template)))


class SubscriberList:
    """Manage subscriber list with tags and unsubscribe."""

    def __init__(self):
        self.subscribers: Dict[str, Subscriber] = {}

    def add(self, email: str, name: str = "", tags: List[str] = None) -> Subscriber:
        sub = Subscriber(email=email, name=name, tags=tags or [],
                         subscribed_at=datetime.now().isoformat())
        self.subscribers[email] = sub
        return sub

    def remove(self, email: str):
        if email in self.subscribers:
            self.subscribers[email].unsubscribed = True

    def get_by_tag(self, tag: str) -> List[Subscriber]:
        return [s for s in self.subscribers.values() if tag in s.tags and not s.unsubscribed]

    def get_active(self) -> List[Subscriber]:
        return [s for s in self.subscribers.values() if not s.unsubscribed]

    def count(self) -> int:
        return len(self.get_active())


class EmailCampaignManager:
    """Manage email campaigns with templates, scheduling, and tracking."""

    def __init__(self, smtp_host: str = "", smtp_port: int = 587,
                 smtp_user: str = "", smtp_pass: str = "",
                 from_email: str = "", from_name: str = ""):
        self.smtp_host = smtp_host
        self.smtp_port = smtp_port
        self.smtp_user = smtp_user
        self.smtp_pass = smtp_pass
        self.from_email = from_email
        self.from_name = from_name
        self.templates: Dict[str, EmailTemplate] = {}
        self.lists: Dict[str, SubscriberList] = {}
        self.campaigns: Dict[str, Campaign] = {}
        self.tracking_pixels: Dict[str, Dict] = {}

    def add_template(self, template: EmailTemplate):
        if not template.variables:
            template.variables = TemplateEngine.extract_variables(template.body_html)
        self.templates[template.name] = template

    def create_list(self, name: str) -> SubscriberList:
        lst = SubscriberList()
        self.lists[name] = lst
        return lst

    def create_campaign(self, campaign_id: str, name: str, template_name: str,
                        list_name: str, scheduled_at: str = "") -> Campaign:
        lst = self.lists.get(list_name, SubscriberList())
        recipients = [s.email for s in lst.get_active()]
        campaign = Campaign(
            id=campaign_id, name=name, template_name=template_name,
            recipients=recipients, scheduled_at=scheduled_at,
        )
        self.campaigns[campaign_id] = campaign
        return campaign

    def send_campaign(self, campaign_id: str, variables: Dict = None) -> Tuple[int, int]:
        """Send campaign emails. Returns (sent, failed)."""
        campaign = self.campaigns.get(campaign_id)
        if not campaign:
            return 0, 0

        template = self.templates.get(campaign.template_name)
        if not template:
            return 0, 0

        variables = variables or {}
        sent = 0
        failed = 0

        for email in campaign.recipients:
            try:
                # Render template
                sub = self._find_subscriber(email)
                render_vars = {**variables, "email": email, "name": sub.name if sub else ""}
                subject = TemplateEngine.render(template.subject, render_vars)
                body = TemplateEngine.render(template.body_html, render_vars)

                # Add tracking pixel
                pixel_id = f"pixel_{campaign_id}_{email}"
                self.tracking_pixels[pixel_id] = {
                    "campaign": campaign_id, "email": email,
                    "opened": False, "clicked": False,
                }
                body += f'<img src="https://track.example.com/pixel/{pixel_id}" width="1" height="1" />'

                # Build email
                msg = MIMEMultipart("alternative")
                msg["Subject"] = subject
                msg["From"] = f"{self.from_name} <{self.from_email}>" if self.from_name else self.from_email
                msg["To"] = email
                msg.attach(MIMEText(template.body_text or "Enable HTML to view this email.", "plain"))
                msg.attach(MIMEText(body, "html"))

                # Send via SMTP if configured
                if self.smtp_host:
                    with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                        server.starttls()
                        server.login(self.smtp_user, self.smtp_pass)
                        server.send_message(msg)

                sent += 1
            except Exception:
                failed += 1

        campaign.sent = sent
        campaign.failed = failed
        campaign.sent_at = datetime.now().isoformat()
        return sent, failed

    def track_open(self, pixel_id: str):
        if pixel_id in self.tracking_pixels:
            self.tracking_pixels[pixel_id]["opened"] = True
            campaign = self.campaigns.get(self.tracking_pixels[pixel_id]["campaign"])
            if campaign:
                campaign.opened += 1

    def track_click(self, pixel_id: str):
        if pixel_id in self.tracking_pixels:
            self.tracking_pixels[pixel_id]["clicked"] = True
            campaign = self.campaigns.get(self.tracking_pixels[pixel_id]["campaign"])
            if campaign:
                campaign.clicked += 1

    def _find_subscriber(self, email: str) -> Optional[Subscriber]:
        for lst in self.lists.values():
            if email in lst.subscribers:
                return lst.subscribers[email]
        return None

    def stats(self) -> Dict:
        return {
            "templates": len(self.templates),
            "lists": len(self.lists),
            "campaigns": len(self.campaigns),
            "total_subscribers": sum(l.count() for l in self.lists.values()),
        }
