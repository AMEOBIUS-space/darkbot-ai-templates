#!/usr/bin/env python3
"""Demo: Notification Hub — multi-channel notifications."""
import sys, os, json
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))
from notifications import NotificationHub, ChannelType

hub = NotificationHub()

# Register channels
hub.register_channel("telegram", ChannelType.TELEGRAM, {"bot_token": "BOT_TOKEN", "chat_id": "CHAT_ID"})
hub.register_channel("discord", ChannelType.DISCORD, {"webhook_url": "WEBHOOK_URL"})
hub.register_channel("slack", ChannelType.SLACK, {"webhook_url": "WEBHOOK_URL"}, enabled=False)
hub.register_channel("log", ChannelType.LOG)

# Templates
hub.add_template("alert", "🚨 Alert: {{service}}", "Service {{service}} is {{status}} at {{time}}")
hub.add_template("deploy", "🚀 Deploy: {{app}}", "App {{app}} v{{version}} deployed to {{env}}")

# Send via log channel (works without external APIs)
notif = hub.send("Welcome", "Hello from Notification Hub!", "log")
print(f"Log: delivered={notif.delivered}")

# Send templated
notif = hub.send_templated("alert", {"service": "API", "status": "down", "time": "12:00"}, "log")
print(f"Alert: {notif.title} | delivered={notif.delivered}")

notif = hub.send_templated("deploy", {"app": "DarkBot", "version": "2.0.0", "env": "production"}, "log")
print(f"Deploy: {notif.title} | delivered={notif.delivered}")

# Broadcast
results = hub.broadcast("System Alert", "All services operational")
print(f"\nBroadcast: {len(results)} channels, {sum(1 for r in results if r.delivered)} delivered")

# Rate limit test
hub.register_channel("limited", ChannelType.LOG, rate_limit=2)
hub.send("T", "1", "limited")
hub.send("T", "2", "limited")
limited = hub.send("T", "3", "limited")
print(f"\nRate limited: delivered={limited.delivered} error={limited.error}")

print(f"\nStats: {json.dumps(hub.stats(), indent=2)}")
