# Plugin Loader: Extensible Apps Without a Framework

> Part of the [darkbot-templates](https://github.com/AMEOBIUS-space/darkbot-ai-templates) series — zero-dependency production templates.

Plugins let users extend your app without modifying core code. This template discovers plugins from directories, resolves dependencies, and routes hooks — all with stdlib `importlib`.

## Usage

```python
from darkbot_templates.templates.plugin_loader import PluginLoader

loader = PluginLoader(plugin_dirs=["./plugins"])

# Discover and load all plugins
loaded = loader.load_all()

for plugin in loaded:
    print(f"  {plugin.name} v{plugin.version} — {plugin.description}")
    print(f"    Hooks: {list(plugin.hooks.keys())}")
```

## Plugin Structure

```
plugins/
├── my_plugin/
│   ├── __init__.py     # must define register(plugin) function
│   └── handlers.py
├── another_plugin/
│   └── __init__.py
```

## Writing a Plugin

```python
# plugins/alert_bot/__init__.py

def register(plugin):
    plugin.name = "alert_bot"
    plugin.version = "1.0.0"
    plugin.description = "Sends alerts when bids are accepted"
    plugin.dependencies = ["telegram_bot"]

    @plugin.hook("bid.accepted")
    def on_accepted(bid_data):
        send_telegram(f"Bid accepted: {bid_data['platform']}")

    @plugin.hook("bid.rejected")
    def on_rejected(bid_data):
        send_telegram(f"Bid rejected: {bid_data['platform']}")
```

## Hook System

```python
loader = PluginLoader(["./plugins"])
loader.load_all()

# Fire a hook — all plugins that registered it get called
results = loader.fire_hook("bid.accepted", {"platform": "kwork", "amount": 500})
# → [{"plugin": "alert_bot", "result": "sent"}, ...]

# Fire with multiple arguments
results = loader.fire_hook("message.received", sender="client", text="Hello")
```

## Dependency Resolution

Plugins declare dependencies — the loader loads them in order:

```python
# plugins/telegram_bot/__init__.py
def register(plugin):
    plugin.name = "telegram_bot"
    plugin.dependencies = []  # no deps, loads first

# plugins/alert_bot/__init__.py
def register(plugin):
    plugin.name = "alert_bot"
    plugin.dependencies = ["telegram_bot"]  # loads after telegram_bot
```

If a dependency is missing, the plugin is marked with an error and skipped:

```python
for p in loader.plugins:
    if p.error:
        print(f"FAILED: {p.name} — {p.error}")
```

## Hot-Reload

```python
# Reload a single plugin after code change
loader.reload("alert_bot")

# Reload all plugins
loader.reload_all()
```

## Plugin Metadata

```python
for plugin in loader.plugins:
    info = plugin.to_dict()
    print(info)
    # {
    #   "name": "alert_bot",
    #   "version": "1.0.0",
    #   "author": "ameobius",
    #   "description": "Sends alerts",
    #   "dependencies": ["telegram_bot"],
    #   "loaded": True,
    #   "error": None,
    #   "hook_count": 2
    # }
```

## Freelance Platform Plugin System

```python
loader = PluginLoader(["./plugins"])
loader.load_all()

# Core fires events, plugins handle them
def on_new_job(job):
    loader.fire_hook("job.discovered", job)

def on_bid_accepted(platform, job_id, amount):
    loader.fire_hook("bid.accepted", {
        "platform": platform,
        "job_id": job_id,
        "amount": amount,
    })

# Plugins: alert_bot, stats_tracker, auto_bidder, discord_notify
```

## Security Considerations

- Plugins execute arbitrary Python — only load plugins you trust
- Sandbox by running plugins in a subprocess if isolation is needed
- Validate `register()` return values before acting on them

## Testing

```bash
pytest tests/test_templates.py -k plugin -v
```

## References

- [importlib docs](https://docs.python.org/3/library/importlib.html)
- [Pluggy](https://pluggy.readthedocs.io/) — pytest's plugin system
- [Hermes Agent Plugins](https://hermes-agent.nousresearch.com/docs) — real-world plugin architecture

---

*darkbot-templates v1.8.5 — 30 templates, zero dependencies, 448 tests.*
