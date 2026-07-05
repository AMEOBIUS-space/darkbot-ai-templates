#!/usr/bin/env python3
"""Demo for Captcha Solver Template — shows multi-provider solving flow."""
import time

def demo():
    print("=" * 50)
    print("🔐 DarkBot AI — Captcha Solver Demo")
    print("=" * 50)
    print()
    
    captchas = [
        {"type": "reCAPTCHA v2", "provider": "2Captcha", "site_key": "6Le-wvkS...", "url": "https://example.com/login"},
        {"type": "hCaptcha", "provider": "CapSolver", "site_key": "a5f74b19-...", "url": "https://example.com/register"},
        {"type": "Cloudflare Turnstile", "provider": "CapSolver", "site_key": "0x4AAA...", "url": "https://protected.com"},
        {"type": "Yandex SmartCaptcha", "provider": "CDP click", "site_key": "ysc1_...", "url": "https://kwork.ru"},
    ]
    
    print(f"🎯 Supported: {len(captchas)} captcha types")
    for c in captchas:
        print(f"  → {c['type']} via {c['provider']}")
    print()
    
    # Simulate solving
    for c in captchas:
        print(f"🔧 Solving {c['type']}...")
        print(f"  → Submitting to {c['provider']}")
        print(f"  → Polling for result...")
        time.sleep(0.5)
        
        if c["provider"] == "CDP click":
            print(f"  → CDP mouse click on checkbox at (298, 276)")
            print(f"  ✅ Solved! (CDP approach, 0.5s)")
        else:
            print(f"  ✅ Solved! Token: 03AGdBq25... (8.2s)")
        print()
    
    print("✅ Multi-provider: 2Captcha + CapSolver + CDP")
    print("✅ Supported: reCAPTCHA v2, hCaptcha, Turnstile, Yandex")
    print("Buy template: @darkbot_ai_bot | $79 | BTC/USDT/ETH/XMR")
    print("=" * 50)

if __name__ == "__main__":
    demo()
