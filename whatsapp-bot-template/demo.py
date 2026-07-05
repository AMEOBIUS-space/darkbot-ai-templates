#!/usr/bin/env python3
"""Demo for WhatsApp Bot Template — simulates commands, rate limiting, media."""
import asyncio, time

async def demo():
    print("=" * 50)
    print("💬 DarkBot AI — WhatsApp Bot Demo")
    print("=" * 50)
    print()
    
    print("📡 Connecting via Baileys (Node.js)...")
    print("  → QR code displayed in terminal")
    print("  → Phone scanned QR")
    print("  → Connected! Session saved.")
    print()
    
    # Simulate /start
    print("👤 +1234567890: /start")
    print("  🤖 Hello! I'm DarkBot AI. How can I help you today?")
    print()
    
    # Simulate /help
    print("👤 +1234567890: /help")
    print("  🤖 Commands: /start, /help, /info")
    print("  🤖 Contact: @darkbot_ai_bot")
    print()
    
    # Simulate /info
    print("👤 +1234567890: /info")
    print("  🤖 DarkBot AI — WhatsApp bot template")
    print("  🤖 Payment: BTC/USDT/ETH/XMR")
    print()
    
    # Simulate rate limiting
    print("👤 Rate limit test (10 msgs in 10s):")
    for i in range(12):
        status = "✅ allowed" if i < 10 else "❌ rate limited"
        print(f"  Msg {i+1}: {status}")
    print()
    
    # Simulate media send
    print("👤 send_media(+1234567890, price_list.pdf)")
    print("  🤖 ✅ Media sent (price_list.pdf)")
    print()
    
    print("✅ Features: Baileys, commands, rate limit, media, groups")
    print("Buy template: @darkbot_ai_bot | $59 | BTC/USDT/ETH/XMR")
    print("=" * 50)

if __name__ == "__main__":
    asyncio.run(demo())
