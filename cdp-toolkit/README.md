# CDP Toolkit

> Chrome DevTools Protocol automation without external dependencies

## Features

- CDPClient — HTTP endpoint for tab management (list, create, close, activate)
- CDPMouseEvents — mouse click, release, move params
- CDPInput — text injection, key events, React/Vue native setter JS
- CDPNavigation — navigate, evaluate JS, screenshot params
- Pure Python stdlib — no playwright, no selenium, no puppeteer

## Quick Start

```python
from cdp_client import CDPClient, CDPInput

client = CDPClient("127.0.0.1", 9222)
targets = client.list_targets()
```

## React Form Fill

```python
from cdp_client import CDPInput

js = CDPInput.native_setter_js("#email", "user@example.com")
# Send via CDP Runtime.evaluate
```

## Tests

```bash
python -m pytest tests/ -v
```

## License

MIT
