#!/usr/bin/env python3
"""Crypto Trading Bot Template — DEX/CEX arbitrage, signal-based, backtesting."""
import asyncio, json, logging, os, time, hmac, hashlib
from dataclasses import dataclass, field
from typing import Optional, List
import aiohttp

logging.basicConfig(level=logging.INFO)

@dataclass
class Order:
    symbol: str
    side: str  # buy, sell
    price: float
    amount: float
    exchange: str
    timestamp: float = field(default_factory=time.time)
    status: str = "pending"  # pending, filled, cancelled

@dataclass
class Signal:
    symbol: str
    action: str  # buy, sell, hold
    strength: float  # 0-1
    source: str  # rsi, macd, arbitrage, manual
    price: float
    timestamp: float = field(default_factory=time.time)

class TradingBot:
    """Multi-exchange crypto trading bot with signal-based execution."""
    
    def __init__(self, config: dict):
        self.config = config
        self.orders: List[Order] = []
        self.signals: List[Signal] = []
        self.positions = {}
        self.session = None
    
    async def connect(self):
        self.session = aiohttp.ClientSession()
    
    async def close(self):
        if self.session:
            await self.session.close()
    
    # === CEX APIs ===
    async def binance_price(self, symbol: str = "BTCUSDT") -> Optional[float]:
        """Get Binance price."""
        async with self.session.get(f"https://api.binance.com/api/v3/ticker/price?symbol={symbol}") as resp:
            if resp.status == 200:
                data = await resp.json()
                return float(data["price"])
        return None
    
    async def okx_price(self, symbol: str = "BTC-USDT") -> Optional[float]:
        """Get OKX price."""
        async with self.session.get(f"https://www.okx.com/api/v5/market/ticker?instId={symbol}") as resp:
            if resp.status == 200:
                data = await resp.json()
                if data.get("data"):
                    return float(data["data"][0]["last"])
        return None
    
    async def bybit_price(self, symbol: str = "BTCUSDT") -> Optional[float]:
        """Get Bybit price."""
        async with self.session.get(f"https://api.bybit.com/v5/market/tickers?category=spot&symbol={symbol}") as resp:
            if resp.status == 200:
                data = await resp.json()
                if data.get("result", {}).get("list"):
                    return float(data["result"]["list"][0]["lastPrice"])
        return None
    
    # === Arbitrage ===
    async def check_arbitrage(self, symbol_map: dict) -> Optional[Signal]:
        """Check price difference across exchanges."""
        prices = {}
        for exchange, symbol in symbol_map.items():
            if exchange == "binance":
                prices["binance"] = await self.binance_price(symbol)
            elif exchange == "okx":
                prices["okx"] = await self.okx_price(symbol)
            elif exchange == "bybit":
                prices["bybit"] = await self.bybit_price(symbol)
        
        prices = {k: v for k, v in prices.items() if v is not None}
        if len(prices) < 2:
            return None
        
        min_exchange = min(prices, key=prices.get)
        max_exchange = max(prices, key=prices.get)
        spread = (prices[max_exchange] - prices[min_exchange]) / prices[min_exchange]
        
        if spread > self.config.get("min_spread", 0.002):  # 0.2% minimum
            signal = Signal(
                symbol=list(symbol_map.values())[0],
                action="buy" if spread > 0 else "sell",
                strength=min(spread * 100, 1.0),
                source="arbitrage",
                price=prices[min_exchange]
            )
            self.signals.append(signal)
            logging.info(f"ARB: buy {min_exchange} @ {prices[min_exchange]}, sell {max_exchange} @ {prices[max_exchange]}, spread {spread*100:.2f}%")
            return signal
        return None
    
    # === Technical Indicators ===
    async def get_klines(self, symbol: str, interval: str = "1h", limit: int = 100) -> List[list]:
        """Get candlestick data from Binance."""
        async with self.session.get(
            f"https://api.binance.com/api/v3/klines?symbol={symbol}&interval={interval}&limit={limit}"
        ) as resp:
            if resp.status == 200:
                return await resp.json()
        return []
    
    def rsi(self, prices: List[float], period: int = 14) -> float:
        """Calculate RSI."""
        if len(prices) < period + 1:
            return 50.0
        gains, losses = [], []
        for i in range(1, len(prices)):
            change = prices[i] - prices[i-1]
            gains.append(max(change, 0))
            losses.append(max(-change, 0))
        avg_gain = sum(gains[-period:]) / period
        avg_loss = sum(losses[-period:]) / period
        if avg_loss == 0:
            return 100.0
        rs = avg_gain / avg_loss
        return 100 - (100 / (1 + rs))
    
    async def rsi_signal(self, symbol: str = "BTCUSDT") -> Optional[Signal]:
        """Generate RSI-based signal."""
        klines = await self.get_klines(symbol)
        if not klines:
            return None
        prices = [float(k[4]) for k in klines]  # close price
        rsi_val = self.rsi(prices)
        
        if rsi_val < 30:
            return Signal(symbol=symbol, action="buy", strength=(30-rsi_val)/30, source="rsi", price=prices[-1])
        elif rsi_val > 70:
            return Signal(symbol=symbol, action="sell", strength=(rsi_val-70)/30, source="rsi", price=prices[-1])
        return Signal(symbol=symbol, action="hold", strength=0.5, source="rsi", price=prices[-1])
    
    # === Execution (template) ===
    async def execute_order(self, signal: Signal, amount: float) -> Order:
        """Execute order (template — implement with exchange API keys)."""
        order = Order(
            symbol=signal.symbol,
            side=signal.action,
            price=signal.price,
            amount=amount,
            exchange=self.config.get("exchange", "binance")
        )
        logging.info(f"ORDER: {signal.action} {amount} {signal.symbol} @ {signal.price} ({signal.source})")
        # Implement actual order placement via exchange API
        self.orders.append(order)
        return order
    
    # === Main loop ===
    async def run(self, symbol: str = "BTCUSDT", interval: int = 60):
        """Run trading bot loop."""
        await self.connect()
        logging.info(f"Bot started: {symbol}, interval {interval}s")
        
        while True:
            try:
                # RSI signal
                sig = await self.rsi_signal(symbol)
                if sig and sig.action != "hold":
                    logging.info(f"Signal: {sig.action} {sig.symbol} (RSI strength: {sig.strength:.2f})")
                    if sig.strength > self.config.get("min_signal_strength", 0.5):
                        await self.execute_order(sig, self.config.get("order_size", 0.001))
                
                # Arbitrage check
                arb = await self.check_arbitrage({
                    "binance": symbol,
                    "okx": symbol.replace("USDT", "-USDT"),
                    "bybit": symbol
                })
                if arb:
                    logging.info(f"Arbitrage opportunity: {arb.strength*100:.2f}%")
                
            except Exception as e:
                logging.error(f"Loop error: {e}")
            
            await asyncio.sleep(interval)

async def main():
    config = {
        "exchange": "binance",
        "min_spread": 0.003,
        "min_signal_strength": 0.5,
        "order_size": 0.001,
    }
    bot = TradingBot(config)
    
    # Demo: check prices
    await bot.connect()
    btc = await bot.binance_price("BTCUSDT")
    print(f"BTC/USDT: ${btc:,.2f}")
    
    rsi = await bot.rsi_signal("BTCUSDT")
    if rsi:
        print(f"RSI signal: {rsi.action} (strength: {rsi.strength:.2f})")
    
    await bot.close()
    print("Trading bot template ready. Configure API keys for live trading.")

if __name__ == "__main__":
    asyncio.run(main())
