#!/usr/bin/env python3
"""Demo for Tor .onion Marketplace Script."""
import json
def demo():
    print("=" * 50)
    print("🌐 DarkBot AI — Tor .onion Marketplace Demo")
    print("=" * 50)
    print()
    
    # Simulate listings
    listings = [
        {"title": "Custom Python Bot", "price": "0.5 XMR", "vendor": "darkbot", "category": "services"},
        {"title": "Web Scraper Script", "price": "0.3 XMR", "vendor": "darkbot", "category": "services"},
        {"title": "Tor Hidden Service Setup", "price": "0.8 XMR", "vendor": "darkbot", "category": "hosting"},
    ]
    
    print("📦 Listings:")
    for l in listings:
        print(f"  {l['title']} | {l['price']} | @{l['vendor']} | {l['category']}")
    print()
    
    # Simulate order
    print("🛒 Order placed: Custom Python Bot")
    print("  → Status: escrow")
    print("  → Escrow address: 4darkbotai...")
    print("  → Amount: 0.5 XMR")
    print()
    
    # Payment
    print("💰 Payment received:")
    print("  → TX: a1b2c3d4...")
    print("  → Status: shipped → completed")
    print()
    
    print("✅ Features: listings, search, escrow, XMR/BTC, orders, stats")
    print("Buy template: @darkbot_ai_bot | $99 | BTC/USDT/ETH/XMR")
    print("=" * 50)

if __name__ == "__main__":
    demo()
