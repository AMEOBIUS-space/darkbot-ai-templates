# Crypto Wallet Monitor

> Track BTC/ETH/XMR wallet balances, transactions, and portfolio value

## Features

- Multi-chain support: BTC (blockchain.info), ETH (etherscan), XMR (xmrchain)
- Balance tracking with change detection
- Transaction logging (incoming/outgoing/internal)
- Low balance threshold alerts
- Portfolio value calculation (with price feed)
- Unread alert management
- Statistics dashboard

## Quick Start

```python
from monitor import WalletMonitor

mon = WalletMonitor()
mon.add_wallet("1A1zP1eP...", "BTC", "Savings")
mon.add_wallet("0x742d...", "ETH", "Trading")
mon.set_balance_threshold("1A1zP1eP...", "BTC", 0.01)

portfolio = mon.get_portfolio_value({"BTC": 62000, "ETH": 3200})
print(f"Total: ${portfolio['total_usd']}")
```

## Tests

```bash
python -m pytest tests/ -v
```

## License

MIT

Freelance portfolio: [https://ameobius-space.github.io/kwork-portfolio/](https://ameobius-space.github.io/kwork-portfolio/)
