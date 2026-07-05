#!/usr/bin/env python3
"""Demo for AI Automation Agent — simulates email, CRM, report tasks."""
import json

def demo():
    print("=" * 50)
    print("🧠 DarkBot AI — AI Automation Agent Demo")
    print("=" * 50)
    print()
    
    # Email auto-reply
    print("📧 Task 1: Email Auto-Reply")
    print("  Input: subject='Meeting request', body='Can we schedule next week?'")
    print("  AI: 'Hi! I'd be happy to schedule a meeting. I'm available Mon-Wed...'")
    print("  ✅ Reply generated (0.8s)")
    print()
    
    # CRM entry
    print("📊 Task 2: CRM Data Entry")
    print("  Input: 'John Doe, john@example.com, interested in TG bot, budget $500'")
    print("  AI: {name: 'John Doe', email: 'john@example.com', interest: 'TG bot', budget: 500}")
    print("  ✅ CRM fields extracted (0.5s)")
    print()
    
    # Report generation
    print("📈 Task 3: Weekly Report")
    print("  Input: 150 customer interactions, 23 new leads, 5 conversions")
    print("  AI: 'Weekly Summary: 150 interactions (+12%), 23 leads, 5 conversions (21.7%)...'")
    print("  ✅ Report generated (1.2s)")
    print()
    
    # n8n webhook
    print("🔗 Task 4: n8n Webhook Integration")
    print("  POST /webhook → AI processes → returns result")
    print("  ✅ Webhook ready at :8080")
    print()
    
    print("✅ Features: OpenAI, email auto-reply, CRM, reports, n8n, webhooks")
    print("Buy template: @darkbot_ai_bot | $59 | BTC/USDT/ETH/XMR")
    print("=" * 50)

if __name__ == "__main__":
    demo()
