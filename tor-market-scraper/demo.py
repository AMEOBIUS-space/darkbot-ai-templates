#!/usr/bin/env python3
"""Demo for Tor Market Scraper — simulates .onion marketplace monitoring."""
import json

def demo():
    print("=" * 50)
    print("🕷 DarkBot AI — Tor Market Scraper Demo")
    print("=" * 50)
    print()
    
    print("📡 Connecting via Tor SOCKS5 (127.0.0.1:9050)...")
    print("  → Circuit established")
    print()
    
    # Mock listings
    listings = [
        {"title": "Digital Product A", "price": "0.005 BTC", "vendor": "seller1", "rating": 4.8, "sales": 234},
        {"title": "Digital Product B", "price": "0.012 BTC", "vendor": "seller2", "rating": 4.5, "sales": 89},
        {"title": "Digital Product C", "price": "0.003 XMR", "vendor": "seller3", "rating": 5.0, "sales": 567},
    ]
    
    print(f"📦 Scraped {len(listings)} listings:")
    for l in listings:
        print(f"  → {l['title']} | {l['price']} | ⭐{l['rating']} | {l['sales']} sales")
    print()
    
    # Pagination
    print("📄 Pagination: 3 pages scraped (15 listings total)")
    print("  → Rate limit: 3s between requests")
    print()
    
    # Price monitor
    print("📊 Price monitoring (continuous mode):")
    print("  → Checking every 3600s")
    print("  → Alert if price drops >10%")
    print()
    
    # Export
    print("📤 Export:")
    print(f"  → JSON: listings.json ({len(listings)} entries)")
    print(f"  → CSV: listings.csv ({len(listings)} rows)")
    print()
    
    print("✅ Tor SOCKS5, extraction, pagination, price monitor, export")
    print("Buy template: @darkbot_ai_bot | $69 | BTC/USDT/ETH/XMR")
    print("=" * 50)

if __name__ == "__main__":
    demo()
