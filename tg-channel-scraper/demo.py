#!/usr/bin/env python3
"""Demo for TG Channel Scraper — simulates multi-channel keyword monitoring."""
import json, time
from datetime import datetime, timedelta

def demo():
    print("=" * 50)
    print("📢 DarkBot AI — TG Channel Scraper Demo")
    print("=" * 50)
    print()
    
    channels = ["it_zakazy", "job_programming", "freelance_webmasters"]
    keywords = ["python", "bot", "parser", "ai", "automation"]
    
    print(f"📡 Monitoring {len(channels)} channels for {len(keywords)} keywords:")
    for ch in channels:
        print(f"  → @{ch}")
    print()
    
    # Mock scraped messages
    mock_msgs = [
        {"channel": "it_zakazy", "text": "Нужен Python бот для Telegram, бюджет 50к", "views": 233, "matched": ["python", "bot"]},
        {"channel": "job_programming", "text": "AI automation specialist wanted", "views": 45, "matched": ["ai", "automation"]},
        {"channel": "freelance_webmasters", "text": "Ищу parser для маркетплейса", "views": 120, "matched": ["parser"]},
    ]
    
    print("📥 Scraped messages (last 24h):")
    for m in mock_msgs:
        print(f"  [@{m['channel']}] {m['text'][:50]}...")
        print(f"    Views: {m['views']} | Keywords: {', '.join(m['matched'])}")
    print()
    
    # Analytics
    total = len(mock_msgs)
    total_views = sum(m["views"] for m in mock_msgs)
    keyword_counts = {}
    for m in mock_msgs:
        for kw in m["matched"]:
            keyword_counts[kw] = keyword_counts.get(kw, 0) + 1
    
    print("📊 Analytics:")
    print(f"  Total messages: {total}")
    print(f"  Total views: {total_views}")
    print(f"  Keyword counts: {json.dumps(keyword_counts)}")
    print()
    
    print("📤 Export: scraped.json + scraped.csv")
    print()
    
    print("✅ Multi-channel, keyword filter, analytics, JSON/CSV export")
    print("Buy template: @darkbot_ai_bot | $49 | BTC/USDT/ETH/XMR")
    print("=" * 50)

if __name__ == "__main__":
    demo()
