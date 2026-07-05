"""Notification Hub — multi-channel notifications (Telegram, Discord, Email, Slack, Webhook)."""
import json
import time
import urllib.request
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass, asdict, field
from datetime import datetime
from enum import Enum


class ChannelType(Enum):
    TELEGRAM = "telegram"
    DISCORD = "discord"
    EMAIL = "email"
    SLACK = "slack"
    WEBHOOK = "webhook"
    LOG = "log"


@dataclass
class Notification:
    id: str
    title: str
    message: str
    channel: str
    priority: str = "normal"  # low, normal, high, critical
    metadata: Dict = field(default_factory=dict)
    sent_at: str = ""
    delivered: bool = False
    error: str = ""


@dataclass
class ChannelConfig:
    channel_type: ChannelType
    enabled: bool = True
    config: Dict = field(default_factory=dict)
    rate_limit_per_hour: int = 100


class NotificationHub:
    """Multi-channel notification dispatcher with routing and templates."""

    def __init__(self):
        self.channels: Dict[str, ChannelConfig] = {}
        self.notifications: List[Notification] = []
        self.templates: Dict[str, Dict] = {}
        self.routing_rules: List[Dict] = []
        self._send_counts: Dict[str, int] = {}

    def register_channel(self, name: str, channel_type: ChannelType, config: Dict = None,
                         rate_limit: int = 100, enabled: bool = True):
        self.channels[name] = ChannelConfig(
            channel_type=channel_type,
            enabled=enabled,
            config=config or {},
            rate_limit_per_hour=rate_limit,
        )

    def add_template(self, name: str, title_template: str, message_template: str):
        self.templates[name] = {"title": title_template, "message": message_template}

    def render_template(self, template_name: str, variables: Dict) -> tuple:
        tpl = self.templates.get(template_name)
        if not tpl:
            return variables.get("title", "Notification"), variables.get("message", "")
        title = tpl["title"]
        msg = tpl["message"]
        for k, v in variables.items():
            title = title.replace(f"{{{{{k}}}}}", str(v))
            msg = msg.replace(f"{{{{{k}}}}}", str(v))
        return title, msg

    def add_routing_rule(self, condition: str, channel: str):
        """Add routing rule: if priority == 'critical', send to 'alerts'."""
        self.routing_rules.append({"condition": condition, "channel": channel})

    def _resolve_channel(self, priority: str, default_channel: str) -> str:
        for rule in self.routing_rules:
            if rule["condition"] == f"priority=={priority}":
                return rule["channel"]
        return default_channel

    def send(self, title: str, message: str, channel: str = "default",
             priority: str = "normal", metadata: Dict = None) -> Notification:
        """Send a notification to a channel."""
        notification = Notification(
            id=f"notif_{int(time.time() * 1000)}",
            title=title,
            message=message,
            channel=channel,
            priority=priority,
            metadata=metadata or {},
        )

        ch = self.channels.get(channel)
        if not ch:
            notification.error = f"Channel '{channel}' not found"
            self.notifications.append(notification)
            return notification

        if not ch.enabled:
            notification.error = f"Channel '{channel}' disabled"
            self.notifications.append(notification)
            return notification

        # Rate limit check
        count = self._send_counts.get(channel, 0)
        if count >= ch.rate_limit_per_hour:
            notification.error = "Rate limit exceeded"
            self.notifications.append(notification)
            return notification

        # Dispatch based on channel type
        try:
            if ch.channel_type == ChannelType.TELEGRAM:
                self._send_telegram(ch.config, title, message)
            elif ch.channel_type == ChannelType.DISCORD:
                self._send_discord(ch.config, title, message)
            elif ch.channel_type == ChannelType.SLACK:
                self._send_slack(ch.config, title, message)
            elif ch.channel_type == ChannelType.WEBHOOK:
                self._send_webhook(ch.config, title, message)
            elif ch.channel_type == ChannelType.EMAIL:
                pass  # Would use SMTP
            elif ch.channel_type == ChannelType.LOG:
                pass  # Just log

            notification.delivered = True
            notification.sent_at = datetime.now().isoformat()
            self._send_counts[channel] = count + 1
        except Exception as e:
            notification.error = str(e)

        self.notifications.append(notification)
        return notification

    def send_templated(self, template_name: str, variables: Dict,
                       channel: str = "default", priority: str = "normal") -> Notification:
        """Send notification using a template."""
        title, message = self.render_template(template_name, variables)
        return self.send(title, message, channel, priority)

    def broadcast(self, title: str, message: str, priority: str = "normal") -> List[Notification]:
        """Send to all enabled channels."""
        results = []
        for name, ch in self.channels.items():
            if ch.enabled:
                results.append(self.send(title, message, name, priority))
        return results

    def _send_telegram(self, config: Dict, title: str, message: str):
        token = config.get("bot_token", "")
        chat_id = config.get("chat_id", "")
        if token and chat_id:
            url = f"https://api.telegram.org/bot{token}/sendMessage"
            data = json.dumps({"chat_id": chat_id, "text": f"{title}\n{message}"}).encode()
            req = urllib.request.Request(url, data=data, method="POST",
                                         headers={"Content-Type": "application/json"})
            urllib.request.urlopen(req, timeout=10)

    def _send_discord(self, config: Dict, title: str, message: str):
        webhook_url = config.get("webhook_url", "")
        if webhook_url:
            data = json.dumps({"content": f"**{title}**\n{message}"}).encode()
            req = urllib.request.Request(webhook_url, data=data, method="POST",
                                         headers={"Content-Type": "application/json"})
            urllib.request.urlopen(req, timeout=10)

    def _send_slack(self, config: Dict, title: str, message: str):
        webhook_url = config.get("webhook_url", "")
        if webhook_url:
            data = json.dumps({"text": f"*{title}*\n{message}"}).encode()
            req = urllib.request.Request(webhook_url, data=data, method="POST",
                                         headers={"Content-Type": "application/json"})
            urllib.request.urlopen(req, timeout=10)

    def _send_webhook(self, config: Dict, title: str, message: str):
        url = config.get("url", "")
        if url:
            data = json.dumps({"title": title, "message": message}).encode()
            req = urllib.request.Request(url, data=data, method="POST",
                                         headers={"Content-Type": "application/json"})
            urllib.request.urlopen(req, timeout=10)

    def stats(self) -> Dict:
        return {
            "channels": len(self.channels),
            "enabled": sum(1 for c in self.channels.values() if c.enabled),
            "total_sent": len(self.notifications),
            "delivered": sum(1 for n in self.notifications if n.delivered),
            "failed": sum(1 for n in self.notifications if not n.delivered),
            "templates": len(self.templates),
        }
