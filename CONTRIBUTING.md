# Contributing to DarkBot AI Templates

## 🙏 Contributors

- [@AMEOBIUS](https://github.com/AMEOBIUS) — Creator, maintainer

## Adding a New Template

1. Create a new directory: `your-template-name/`
2. Include:
   - `main.py` (or `bot.py`, `scraper.py`) — main code
   - `demo.py` — interactive demo (no API keys needed)
   - `requirements.txt` — dependencies with upper bounds
   - `README.md` — description, price, contact
3. Update root `README.md` table
4. Update `docs/index.html` (portfolio)
5. Add tutorial to `docs/blog/`
6. Update `docs/sitemap.xml`
7. Submit a PR using the PR template

## Template Standards

- Python 3.10+
- Type hints where possible
- Dataclasses for data models
- Async where I/O bound
- Docstrings on all public functions
- requirements.txt with upper bounds (e.g. `>=1.0,<2`)
- Demo must run without API keys

## Code Style

- Follow existing patterns in the repo
- Use `async def` for I/O operations
- Prefer `aiohttp` over `requests`
- Use `dataclasses` for structured data

## Testing

- `python -m py_compile` must pass
- `python demo.py` must run without errors
- CI (GitHub Actions) verifies on every push

## Contact

- Telegram: [@darkbot_ai_bot](https://t.me/darkbot_ai_bot)
- Payment: BTC / USDT / ETH / XMR
- Discussions: [GitHub Discussions](https://github.com/AMEOBIUS/darkbot-ai-templates/discussions)
