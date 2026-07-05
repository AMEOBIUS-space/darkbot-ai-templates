#!/usr/bin/env python3
"""Demo for Crypto Payment Gateway — simulates invoice creation, BTC/XMR verification."""
import json, time, hashlib

def demo():
    print("=" * 50)
    print("💰 DarkBot AI — Crypto Payment Gateway Demo")
    print("=" * 50)
    print()
    
    wallets = {"BTC": "bc1qdarkbotai...", "USDT": "0xDarkBotAI...", "ETH": "0xDarkBotAI...", "XMR": "4DarkBotAI..."}
    
    print("💼 Wallets configured:")
    for cur, addr in wallets.items():
        print(f"  {cur}: {addr[:20]}...")
    print()
    
    # Create invoice
    inv_id = hashlib.sha256(f"{time.time()}TG-Bot".encode()).hexdigest()[:16]
    print(f"🧾 Creating invoice:")
    print(f"  ID: {inv_id}")
    print(f"  Product: TG Bot Template")
    print(f"  Amount: $49 USD")
    print(f"  Currency: BTC")
    print(f"  Address: {wallets['BTC']}")
    print(f"  Expires: 60 minutes")
    print()
    
    # Simulate payment received
    print("⏳ Waiting for payment...")
    print("  → Checking blockchain API every 30s...")
    print("  → TX detected: 0xabc123...")
    print("  → Amount: 0.00073 BTC ($49)")
    print("  → Confirmations: 1")
    print("  ✅ Payment CONFIRMED!")
    print()
    
    # Callbacks
    print("🔔 Notifications:")
    print("  → Webhook POST to https://yourapp.com/payment-webhook")
    print("  → Callback: deliver_product(invoice_id, buyer_email)")
    print("  → Telegram: '💰 Payment received: $49 BTC for TG Bot Template'")
    print()
    
    # XMR invoice
    print(f"🧾 XMR Invoice:")
    print(f"  Amount: 0.73 XMR")
    print(f"  Address: {wallets['XMR'][:20]}...")
    print(f"  → Monero RPC verification")
    print()
    
    print("✅ Features: BTC/USDT/ETH/XMR, invoices, webhooks, FastAPI, callbacks")
    print("Buy template: @darkbot_ai_bot | $69 | BTC/USDT/ETH/XMR")
    print("=" * 50)

if __name__ == "__main__":
    demo()
