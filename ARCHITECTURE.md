# Architecture

## Overview

Each template is self-contained with:
- `main.py` / `bot.py` / `scraper.py` — main code
- `demo.py` — interactive demo (no API keys needed)
- `requirements.txt` — dependencies
- `README.md` — description + pricing

## Template Structure

```
products/
├── tg-bot-template/          # aiogram 3 + OpenAI + FSM
├── web-scraper-template/      # Playwright + proxy rotation
├── ai-automation-template/    # OpenAI + CRM + reports
├── cdp-automation-template/   # Chrome DevTools Protocol
├── solidity-template/         # ERC20 + presale + Foundry
├── fastapi-template/          # JWT + SQLite + WebSocket
├── discord-bot-template/      # discord.py + slash commands
├── proxy-rotation-template/   # async health checks
├── email-scraper-template/    # recursive crawl + export
├── whatsapp-bot-template/     # Baileys + Python orchestration
├── n8n-workflow-template/     # n8n workflow JSON export
├── tg-channel-scraper/        # Telethon + keyword monitor
├── captcha-solver-template/   # 2Captcha + CapSolver
├── crypto-payment-template/   # BTC/USDT/ETH/XMR gateway
├── tor-hidden-service-template/ # v3 onion + nginx + Docker
├── tor-market-scraper/        # .onion monitoring via Tor
├── crypto-trading-bot/        # Binance/OKX/Bybit + RSI
└── onion-marketplace-script/  # listings + escrow + XMR
```

## Design Principles

1. **Self-contained** — no shared dependencies between templates
2. **Async-first** — all I/O uses async/await
3. **Type hints** — Python 3.10+ type annotations
4. **Dataclasses** — structured data models
5. **Runnable demos** — every template has demo.py
6. **No API keys needed for demos** — mock data or public APIs

## CI Pipeline

GitHub Actions verifies on every push:
1. py_compile all Python files
2. Run all demos (timeout 10s each)
3. Check 17+ READMEs exist
4. Check 10+ requirements.txt exist

## Dependencies

Each template has its own `requirements.txt` with upper bounds:
- `aiogram>=3.4,<4`
- `aiohttp>=3.9,<4`
- `playwright>=1.40,<2`
- etc.
