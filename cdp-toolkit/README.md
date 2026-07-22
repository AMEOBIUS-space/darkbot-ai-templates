# CDP Toolkit

[![PyPI](https://img.shields.io/pypi/v/cdp-toolkit)](https://pypi.org/project/cdp-toolkit/)
[![Tests](https://img.shields.io/badge/tests-38%20passing-brightgreen)](tests/)
[![Dependencies](https://img.shields.io/badge/dependencies-zero-success)](https://pypi.org/project/cdp-toolkit/)
[![License](https://img.shields.io/badge/license-MIT-blue)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.10%2B-blue)](https://python.org)

Freelance demos: [https://ameobius-space.github.io/kwork-portfolio/](https://ameobius-space.github.io/kwork-portfolio/)

> Chrome DevTools Protocol automation without external dependencies. No Playwright, no Selenium, no Puppeteer. Pure Python stdlib.

## Install

```bash
pip install cdp-toolkit
```

## Why CDP Toolkit?

| Feature | Playwright | Selenium | **cdp-toolkit** |
|---------|-----------|----------|-----------------|
| Dependencies | 50+ packages | 20+ packages | **0** |
| Install size | ~140MB | ~150MB | **~13KB** |
| Browser download | Yes (~200MB) | Yes (~100MB) | **No** |
| Cold start (import) | ~200ms | ~500ms | **<1ms** |
| Learning curve | Medium | High | **Low** |
| Speed | Fast | Slow | **Fastest** |
| Cloud-native | Yes | Partial | **Yes** |

*Metrics: measured via `scripts/benchmark.py` in CI (artifact: `benchmark_results.json`). cdp-toolkit: 12.6KB package, 0.34ms import, 0.3KB peak RAM on parameter-builder path. Playwright: 140MB package (pip, no browser binary). Run `python scripts/benchmark.py` to reproduce.*

CDP Toolkit talks directly to Chrome's DevTools Protocol via HTTP and WebSocket. You bring your own Chrome instance (local, Docker, or cloud), and CDP Toolkit handles the rest.

## Categories

CDP Toolkit is organized into focused, composable modules:

### CDPClient

The core HTTP client for the Chrome DevTools Protocol. It manages tabs (targets), navigates pages, evaluates JavaScript, and captures screenshots, all without requiring Playwright, Selenium, or external browser drivers.

### CDPInput

Helpers for text input and form handling. It can generate React/Vue/Angular-compatible native setter JavaScript, dispatch key events, and insert text, making it easy to drive forms in modern JavaScript apps.

### CDPMouseEvents

Parameter builders for `Input.dispatchMouseEvent`. It covers clicks, right-clicks, double-clicks, hovers, pointer moves, and drag-and-drop interactions.

### CDPNavigation

Page lifecycle helpers for navigation, evaluation, and screenshots. It builds `Page.navigate`, `Runtime.evaluate`, `Page.captureScreenshot`, and `DOM.scrollIntoView` parameters, and can wait for selectors or elements.

## Usage Examples

### Run the demo

```bash
python demo.py
```

### Connect to a running Chrome instance

```python
from cdp_toolkit import CDPClient

client = CDPClient("127.0.0.1", 9222)
print(client.list_targets())
```

### Fill a React form

```python
from cdp_toolkit import CDPClient, CDPInput

client = CDPClient("127.0.0.1", 9222)
tab = client.create_target("https://example.com")
js = CDPInput.native_setter_js("#email", "user@example.com")
client.evaluate(tab["id"], js)
```

### Click and drag

```python
from cdp_toolkit import CDPClient, CDPMouseEvents

client = CDPClient("127.0.0.1", 9222)
# Click at (200, 300)
client.evaluate(tab_id, CDPMouseEvents.click(200, 300))
# Drag from (100, 100) to (400, 300)
client.evaluate(tab_id, CDPMouseEvents.drag(100, 100, 400, 300))
```

### Navigate and take a screenshot

```python
from cdp_toolkit import CDPClient, CDPNavigation

client = CDPClient("127.0.0.1", 9222)
client.navigate(tab_id, "https://example.com")
b64 = client.screenshot(tab_id)
```

### Run the tests

```bash
python -m pytest tests/ -v
```

## Quick Start

```python
from cdp_toolkit import CDPClient

# Connect to a Chrome instance with --remote-debugging-port=9222
client = CDPClient("127.0.0.1", 9222)

# List open tabs
tabs = client.list_targets()
for tab in tabs:
    print(f"{tab['id'][:8]} | {tab['url'][:60]}")

# Create a new tab
new_tab = client.create_target("https://example.com")

# Navigate
client.navigate(new_tab['id'], "https://httpbin.org/forms/post")

# Execute JavaScript
title = client.evaluate(new_tab['id'], "document.title")
print(f"Page title: {title}")
```

## React/Vue Form Filling

The most common CDP use case: filling forms on React/Vue/Angular sites where standard `input.value = "x"` does not trigger reactivity.

```python
from cdp_toolkit import CDPInput

# Generate native setter JavaScript for React
js_code = CDPInput.native_setter_js(
    selector="#email",
    value="user@example.com"
)
# Execute via CDP — triggers React's onChange handler

# For Vue.js
js_code = CDPInput.vue_setter_js(
    selector="input[name='phone']",
    value="+1234567890"
)

# Key-by-key typing simulation
js_code = CDPInput.simulate_typing(
    selector="#search",
    text="hello world",
    delay_ms=50
)
```

## Mouse Events

```python
from cdp_toolkit import CDPMouseEvents

# Click at coordinates
params = CDPMouseEvents.click(x=200, y=300)

# Right-click
params = CDPMouseEvents.click(x=200, y=300, button="right")

# Double-click
params = CDPMouseEvents.double_click(x=200, y=300)

# Drag and drop
params = CDPMouseEvents.drag(
    start_x=100, start_y=200,
    end_x=400, end_y=300
)
```

## Navigation and Screenshots

```python
from cdp_toolkit import CDPNavigation

# Navigate and wait for load
client.navigate_and_wait(tab_id, "https://example.com")

# Take screenshot
screenshot_b64 = client.screenshot(tab_id)

# Scroll to element
js = CDPNavigation.scroll_to_element("#footer")
client.evaluate(tab_id, js)

# Wait for selector
js = CDPNavigation.wait_for_selector(".result-card", timeout_ms=5000)
```

## Anti-Detection

CDP Toolkit includes JavaScript snippets to make automation less detectable:

```python
from cdp_toolkit import stealth

# Remove webdriver flag
client.evaluate(tab_id, stealth.remove_webdriver_flag())

# Override navigator properties
client.evaluate(tab_id, stealth.override_navigator())

# Add realistic timing jitter
CDPInput.set_typing_delay(min_ms=30, max_ms=120)
```

## Docker Integration

Run Chrome in Docker and control it with CDP Toolkit:

```dockerfile
# Dockerfile
FROM chrome/headless
EXPOSE 9222
CMD ["chrome", "--remote-debugging-port=9222", "--no-sandbox"]
```

```python
# Connect to Docker Chrome
client = CDPClient("chrome-container", 9222)
```

## Testing

```bash
python -m pytest tests/ -v --tb=short
```

39 tests covering all modules. Zero external dependencies in tests.

## API Reference

### CDPClient

| Method | Description |
|--------|-------------|
| `list_targets()` | List all open tabs/pages |
| `create_target(url)` | Open a new tab |
| `close_target(id)` | Close a tab |
| `activate_target(id)` | Focus a tab |
| `navigate(id, url)` | Navigate to URL |
| `evaluate(id, js)` | Execute JavaScript |
| `screenshot(id)` | Capture page screenshot |

### CDPInput

| Method | Description |
|--------|-------------|
| `native_setter_js(sel, val)` | React-compatible value setter |
| `vue_setter_js(sel, val)` | Vue.js-compatible value setter |
| `simulate_typing(sel, text, delay)` | Human-like typing simulation |
| `key_event(key)` | Send keyboard event |

### CDPMouseEvents

| Method | Description |
|--------|-------------|
| `click(x, y, button)` | Mouse click |
| `double_click(x, y)` | Double click |
| `drag(sx, sy, ex, ey)` | Drag and drop |
| `hover(x, y)` | Mouse hover |

## License

MIT — see [LICENSE](LICENSE)

## Links

- [GitHub](https://github.com/AMEOBIUS-team/cdp-toolkit)
- [PyPI](https://pypi.org/project/cdp-toolkit/)
- [Full templates collection](https://github.com/AMEOBIUS-team/darkbot-ai-templates)
