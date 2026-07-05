#!/usr/bin/env python3
"""Demo for Crypto Trading Bot Template — fetches live BTC price + RSI calculation."""
import asyncio, json, urllib.request

async def demo():
    print("=" * 50)
    print("📈 DarkBot AI — Crypto Trading Bot Demo")
    print("=" * 50)
    print()
    
    # Fetch real BTC price from Binance (no API key needed)
    print("📡 Fetching live prices...")
    prices = {}
    
    try:
        req = urllib.request.Request("https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT")
        data = json.loads(urllib.request.urlopen(req, timeout=10).read())
        prices["Binance"] = float(data["price"])
        print(f"  Binance  BTC/USDT: ${prices['Binance']:,.2f}")
    except Exception as e:
        prices["Binance"] = 67000.0
        print(f"  Binance  BTC/USDT: ${prices['Binance']:,.2f} (mock)")
    
    try:
        req = urllib.request.Request("https://api.binance.com/api/v3/ticker/price?symbol=ETHUSDT")
        data = json.loads(urllib.request.urlopen(req, timeout=10).read())
        prices["ETH"] = float(data["price"])
        print(f"  Binance  ETH/USDT: ${prices['ETH']:,.2f}")
    except:
        prices["ETH"] = 3500.0
        print(f"  Binance  ETH/USDT: ${prices['ETH']:,.2f} (mock)")
    
    print()
    
    # RSI calculation demo with mock price history
    mock_prices = [65000, 65500, 64800, 66000, 67000, 66500, 67200, 68000, 67500, 69000,
                   68500, 69500, 70000, 69800, 70500, 71000, 70800, 71500, 72000, 71800]
    
    # Simple RSI
    gains, losses = [], []
    for i in range(1, len(mock_prices)):
        change = mock_prices[i] - mock_prices[i-1]
        gains.append(max(change, 0))
        losses.append(max(-change, 0))
    
    period = 14
    avg_gain = sum(gains[-period:]) / period
    avg_loss = sum(losses[-period:]) / period
    rsi = 100 - (100 / (1 + avg_gain / max(avg_loss, 0.01)))
    
    print(f"📊 RSI (14): {rsi:.1f}")
    if rsi < 30:
        signal = "🟢 BUY (oversold)"
    elif rsi > 70:
        signal = "🔴 SELL (overbought)"
    else:
        signal = "🟡 HOLD (neutral)"
    print(f"  Signal: {signal}")
    print()
    
    # Arbitrage check (mock)
    print("🔄 Arbitrage check:")
    mock_okx = prices["Binance"] * 1.002  # Simulate slight difference
    spread = (mock_okx - prices["Binance"]) / prices["Binance"]
    print(f"  Binance: ${prices['Binance']:,.2f}")
    print(f"  OKX:     ${mock_okx:,.2f}")
    print(f"  Spread:  {spread*100:.2f}%")
    if spread > 0.003:
        print(f"  → ARBITRAGE OPPORTUNITY: Buy Binance, Sell OKX")
    else:
        print(f"  → No arbitrage (spread < 0.3%)")
    print()
    
    print("✅ Features demonstrated:")
    print("  • Live price fetching (Binance API)")
    print("  • RSI technical indicator")
    print("  • Signal generation (buy/sell/hold)")
    print("  • Arbitrage spread detection")
    print()
    print("Full template includes:")
    print("  • Multi-exchange (Binance, OKX, Bybit)")
    print("  • Order execution via API keys")
    print("  • Continuous monitoring loop")
    print("  • Configurable thresholds")
    print()
    print("Buy template: @darkbot_ai_bot | $79 | BTC/USDT/ETH/XMR")
    print("=" * 50)

if __name__ == "__main__":
    asyncio.run(demo())
