#!/usr/bin/env python3
"""Demo for Proxy Rotation Manager — shows rotation, health checks, stats."""
import asyncio, random

async def demo():
    print("=" * 50)
    print("🔄 DarkBot AI — Proxy Rotation Manager Demo")
    print("=" * 50)
    print()
    
    # Mock proxies
    proxies = [
        {"host": "185.199.229.156", "port": 7492, "protocol": "http", "latency": 45},
        {"host": "37.26.86.161", "port": 4718, "protocol": "socks5", "latency": 120},
        {"host": "176.97.114.238", "port": 8080, "protocol": "http", "latency": 80},
        {"host": "46.17.47.48", "port": 4145, "protocol": "socks5", "latency": 200},
    ]
    
    print(f"📊 Proxy pool: {len(proxies)} proxies")
    for p in proxies:
        print(f"  {p['protocol']}://{p['host']}:{p['port']} | {p['latency']}ms")
    print()
    
    # Simulate round-robin
    print("🔄 Round-robin rotation:")
    for i in range(5):
        proxy = proxies[i % len(proxies)]
        print(f"  Request {i+1}: {proxy['protocol']}://{proxy['host']}:{proxy['port']}")
    print()
    
    # Simulate random
    print("🎲 Random rotation:")
    for i in range(3):
        proxy = random.choice(proxies)
        print(f"  Request {i+1}: {proxy['protocol']}://{proxy['host']}:{proxy['port']}")
    print()
    
    # Simulate health check
    print("🏥 Health check:")
    healthy = 0
    for p in proxies:
        ok = random.random() > 0.25  # 75% healthy
        status = "✅ healthy" if ok else "❌ failed"
        print(f"  {p['host']}:{p['port']} → {status} ({p['latency']}ms)")
        if ok: healthy += 1
    print()
    
    # Stats
    print(f"📈 Stats:")
    print(f"  Total: {len(proxies)}")
    print(f"  Healthy: {healthy}")
    print(f"  Unhealthy: {len(proxies) - healthy}")
    avg_lat = sum(p['latency'] for p in proxies) / len(proxies)
    print(f"  Avg latency: {avg_lat:.0f}ms")
    print()
    
    print("✅ Features: round-robin, random, health checks, failover, SOCKS5/4/HTTP")
    print("Buy template: @darkbot_ai_bot | $39 | BTC/USDT/ETH/XMR")
    print("=" * 50)

if __name__ == "__main__":
    asyncio.run(demo())
