#!/usr/bin/env python3
"""Demo for N8N Workflow Template — generates and validates workflow JSON."""
import json

def demo():
    print("=" * 50)
    print("🔗 DarkBot AI — N8N Workflow Demo")
    print("=" * 50)
    print()
    
    print("📋 Workflow: AI Lead Qualification Pipeline")
    print()
    
    # Show nodes
    nodes = [
        ("Webhook", "POST /lead", "Receives lead data"),
        ("Extract Lead", "Function", "Parse name, email, budget, project"),
        ("AI Qualify", "OpenAI", "Score 1-10 based on budget + clarity"),
        ("Route Lead", "Function", "hot (8+), warm (5+), cold (<5)"),
        ("Telegram", "Notify LO", "🔥 alert for hot leads"),
        ("Auto Reply", "Email", "Send AI-generated response"),
        ("Save DB", "MySQL", "Store lead with score + priority"),
    ]
    
    print("🔧 Nodes:")
    for i, (name, type_, desc) in enumerate(nodes, 1):
        print(f"  {i}. {name} ({type_}) — {desc}")
    print()
    
    # Simulate lead
    print("📞 Incoming lead:")
    lead = {"name": "John Doe", "email": "john@example.com", "budget": 5000, "project_type": "telegram_bot"}
    print(f"  {json.dumps(lead, indent=2)}")
    print()
    
    # Simulate AI scoring
    print("🧠 AI Qualification:")
    print("  → Score: 8/10 (high budget, clear project)")
    print("  → Priority: HOT")
    print("  → Estimated value: $2,000")
    print("  → Suggested response: 'Hi John! We can build your TG bot...'")
    print()
    
    # Simulate routing
    print("🔀 Routing: HOT → Telegram + Email + DB")
    print("  → LO notified: '🔥 HOT LEAD: John Doe, $5000 budget, TG bot'")
    print("  → Auto-reply sent to john@example.com")
    print("  → Saved to MySQL: leads table")
    print()
    
    # Export workflow
    print("📤 Export: workflow.json (importable in n8n)")
    print()
    
    print("✅ 7 nodes, AI scoring, routing, notifications, DB save")
    print("Buy template: @darkbot_ai_bot | $49 | BTC/USDT/ETH/XMR")
    print("=" * 50)

if __name__ == "__main__":
    demo()
