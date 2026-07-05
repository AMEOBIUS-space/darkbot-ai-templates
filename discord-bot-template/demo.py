#!/usr/bin/env python3
"""Demo for Discord Bot Template — simulates slash commands without Discord API."""
import asyncio

async def demo():
    print("=" * 50)
    print("🎮 DarkBot AI — Discord Bot Template Demo")
    print("=" * 50)
    print()
    
    print("📡 Bot online as DarkBot AI#1234")
    print("  → Synced 6 slash commands")
    print()
    
    # Simulate /ping
    print("👤 /ping")
    print("  🤖 Pong! 42ms")
    print()
    
    # Simulate /userinfo
    print("👤 /userinfo @user")
    print("  🤖 Embed: User#1234 | ID: 123456 | Joined: 2024-01-15 | Roles: 3")
    print()
    
    # Simulate /poll
    print("👤 /poll \"Best language?\" Python JavaScript Rust")
    print("  🤖 📊 Best language?")
    print("     1️⃣ Python")
    print("     2️⃣ JavaScript")
    print("     3️⃣ Rust")
    print("  → Reactions added: 1️⃣ 2️⃣ 3️⃣")
    print()
    
    # Simulate /play
    print("👤 /play \"Never Gonna Give You Up\"")
    print("  🤖 Added to queue: Never Gonna Give You Up (position 1)")
    print()
    
    # Simulate /queue
    print("👤 /queue")
    print("  🤖 Queue:")
    print("     1. Never Gonna Give You Up")
    print()
    
    # Simulate /purge (mod)
    print("👤 /purge 5 (mod)")
    print("  🤖 Deleted 5 messages")
    print()
    
    print("✅ 6 slash commands: ping, userinfo, poll, play, queue, purge")
    print("Buy template: @darkbot_ai_bot | $49 | BTC/USDT/ETH/XMR")
    print("=" * 50)

if __name__ == "__main__":
    asyncio.run(demo())
