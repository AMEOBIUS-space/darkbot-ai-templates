#!/usr/bin/env python3
"""Demo: Crypto Wallet Monitor."""
import sys, os, json
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))
from monitor import WalletMonitor, Transaction

mon = WalletMonitor()
mon.add_wallet("1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa", "BTC", "Savings")
mon.add_wallet("0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb1", "ETH", "Trading")
mon.set_balance_threshold("1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa", "BTC", 0.01)

mon.wallets["BTC:1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa"].balance = 0.5
mon.wallets["ETH:0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb1"].balance = 10.0

tx = Transaction("abc123", "BTC", "sender_addr", "1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa",
                 0.25, 0.0001, 6, "2026-07-05T18:00:00Z", "incoming")
mon.add_transaction(tx)

portfolio = mon.get_portfolio_value({"BTC": 62000, "ETH": 3200})
print("=== Portfolio ===")
print(json.dumps(portfolio, indent=2))

print(f"\n=== Alerts ===")
for a in mon.get_alerts():
    print(f"  {a['type']}: {json.dumps({k:v for k,v in a.items() if k != 'type'})}")

print(f"\n=== Stats ===")
print(json.dumps(mon.stats(), indent=2))
