# Signal Handler: Graceful Shutdown for Daemons

> Part of the [darkbot-templates](https://github.com/AMEOBIUS-space/darkbot-ai-templates) series — zero-dependency production templates.

When you kill a process with `Ctrl+C` or `docker stop`, the OS sends a signal. Without a handler, the process dies immediately — in-flight requests dropped, database connections leaked, temp files orphaned. This template gives you graceful shutdown sequences.

## Usage

```python
from darkbot_templates.templates.signal_handler import SignalHandler

sig = SignalHandler(shutdown_timeout=30.0)

# Register cleanup callbacks (priority: lower = runs first)
sig.on_shutdown(close_db, priority=10)
sig.on_shutdown(flush_logs, priority=5)
sig.on_shutdown(close_connections, priority=20)

# Reload on SIGHUP
sig.on_reload(reload_config)

# Install handlers
sig.install()

# Run main loop
try:
    while True:
        process_events()
except KeyboardInterrupt:
    pass

# Or block until signal received
sig.wait_for_shutdown()
# Returns when SIGTERM/SIGINT received
```

## Shutdown Sequence

```
SIGTERM/SIGINT received
  │
  ├─ Run callbacks in priority order (1, 2, 3...)
  │   ├─ flush_logs()
  │   ├─ close_db()
  │   └─ close_connections()
  │
  ├─ Wait for all callbacks to complete
  │
  └─ If timeout (30s): force exit
```

## Priority Ordering

Lower priority numbers run first — critical cleanup before less important:

```python
sig = SignalHandler()

# Priority 1: stop accepting new work
sig.on_shutdown(stop_accepting, priority=1)

# Priority 5: flush pending items
sig.on_shutdown(flush_queue, priority=5)

# Priority 10: close resources
sig.on_shutdown(close_db, priority=10)
sig.on_shutdown(close_redis, priority=10)

# Priority 20: final log
sig.on_shutdown(log_shutdown, priority=20)
```

## SIGHUP Config Reload

```python
sig = SignalHandler()

config = load_config("app.yaml")

@sig.on_reload
def reload():
    global config
    config = load_config("app.yaml")
    print(f"Config reloaded (reload #{sig.reload_count})")

sig.install()

# Send SIGHUP to reload:
# kill -HUP <pid>
```

## Custom Signal Handlers

```python
sig = SignalHandler()

# Handle SIGUSR1 for debug dump
sig.on_signal("SIGUSR1", dump_debug_info)

# Handle SIGUSR2 for stats dump
sig.on_signal("SIGUSR2", dump_stats)

sig.install()
```

## Freelance Bot Lifecycle

```python
from darkbot_templates.templates.signal_handler import SignalHandler
from darkbot_templates.templates.task_queue import TaskQueue

sig = SignalHandler(shutdown_timeout=15.0)
queue = TaskQueue(max_workers=4)
queue.start()

# On shutdown: stop accepting, finish pending, close
sig.on_shutdown(lambda: queue.stop_accepting(), priority=1)
sig.on_shutdown(lambda: queue.join(timeout=10), priority=5)
sig.on_shutdown(db.close, priority=10)
sig.on_shutdown(bot.disconnect, priority=15)

sig.install()

# Run bot
bot.run()
sig.wait_for_shutdown()
```

## Cross-Platform

| Signal | Linux | macOS | Windows |
|--------|-------|-------|---------|
| SIGINT (Ctrl+C) | ✓ | ✓ | ✓ |
| SIGTERM | ✓ | ✓ | ✓ |
| SIGHUP | ✓ | ✓ | Ignored |
| SIGUSR1/2 | ✓ | ✓ | Ignored |

Windows gracefully ignores Unix-only signals — no crashes.

## Testing

```bash
pytest tests/test_templates.py -k signal -v
```

## References

- [Python signal module](https://docs.python.org/3/library/signal.html)
- [Graceful Shutdown Pattern](https://learnk8s.io/graceful-shutdown)

---

*darkbot-templates v1.8.5 — 30 templates, zero dependencies, 448 tests.*
