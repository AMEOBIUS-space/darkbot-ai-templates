#!/usr/bin/env python3
"""Demo: Email Campaign Automation."""
import sys, os, json
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))
from campaign import EmailCampaignManager, EmailTemplate

mgr = EmailCampaignManager(from_email="newsletter@darkbot.ai", from_name="DarkBot AI")

# Template
tpl = EmailTemplate(
    "welcome",
    "Welcome to DarkBot AI, {{name}}!",
    "<h1>Welcome, {{name}}!</h1><p>Your code is {{code}}.</p><p>Visit <a href='{{url}}'>{{url}}</a></p>",
)
mgr.add_template(tpl)

# Subscriber list
lst = mgr.create_list("early_adopters")
lst.add("alice@example.com", "Alice", ["vip", "early"])
lst.add("bob@example.com", "Bob", ["early"])
lst.add("charlie@example.com", "Charlie", ["vip"])

print(f"Active subscribers: {lst.count()}")
print(f"VIP subscribers: {len(lst.get_by_tag('vip'))}")

# Campaign
campaign = mgr.create_campaign("c1", "Welcome Campaign", "welcome", "early_adopters")
print(f"Campaign recipients: {len(campaign.recipients)}")

# Send (no SMTP configured — tracks sends only)
sent, failed = mgr.send_campaign("c1", {"code": "DARK42", "url": "https://darkbot.ai"})
print(f"Sent: {sent}, Failed: {failed}")

# Tracking
mgr.track_open("pixel_c1_alice@example.com")
print(f"Opened: {campaign.opened}")

print(f"\nStats: {json.dumps(mgr.stats(), indent=2)}")
print(f"Campaign: sent={campaign.sent} opened={campaign.opened}")
