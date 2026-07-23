# File Watcher: Cross-Platform Without watchdog

> Part of the [darkbot-templates](https://github.com/AMEOBIUS-space/darkbot-ai-templates) series — zero-dependency production templates.

`watchdog` uses inotify on Linux, FSEvents on macOS, and ReadDirectoryChangesW on Windows. It's fast but adds platform-specific dependencies. This template uses polling — slower, but works everywhere Python runs.

## Usage

```python
from darkbot_templates.templates.file_watcher import FileWatcher

watcher = FileWatcher(poll_interval=2.0)

# Watch files or directories
watcher.watch("/var/log/app.log")
watcher.watch("/data/uploads/")

# Register handlers
watcher.on_modified(lambda path: print(f"Modified: {path}"))
watcher.on_created(lambda path: print(f"New file: {path}"))
watcher.on_deleted(lambda path: print(f"Deleted: {path}"))

# Start watching (runs in daemon thread)
watcher.start()

# ... files change, handlers fire ...

watcher.stop()
```

## Event Types

| Event | Trigger | Handler |
|-------|---------|---------|
| `on_modified` | File mtime changes | `callback(path: str)` |
| `on_created` | New file appears in watched dir | `callback(path: str)` |
| `on_deleted` | File disappears | `callback(path: str)` |
| `on_size_change` | File size changes (growth/shrink) | `callback(path: str)` |

## Chained Handlers

```python
watcher = FileWatcher(poll_interval=1.0)

# Multiple handlers per event
watcher.on_modified(log_change)
watcher.on_modified(reload_config)
watcher.on_modified(notify_team)

watcher.watch("/etc/myapp/config.yaml")
```

## Directory Watching

```python
watcher = FileWatcher(poll_interval=3.0)
watcher.watch("/data/uploads/")

# Fires on_created when a new file lands
watcher.on_created(process_upload)

# Fires on_modified when a file grows (useful for log tailing)
watcher.on_modified(lambda p: print(f"Log grew: {p}"))

watcher.start()
```

## Log Tail Pattern

```python
watcher = FileWatcher(poll_interval=0.5)
watcher.watch("/var/log/app.log")

last_pos = 0

def tail_log(path):
    global last_pos
    with open(path) as f:
        f.seek(last_pos)
        new_lines = f.readlines()
        last_pos = f.tell()
    for line in new_lines:
        process_log_line(line)

watcher.on_modified(tail_log)
watcher.start()
```

## Config Hot-Reload

```python
import json

watcher = FileWatcher(poll_interval=1.0)
watcher.watch("config.json")

def reload_config(path):
    with open(path) as f:
        new_config = json.load(f)
    app.update_config(new_config)
    print("Config reloaded")

watcher.on_modified(reload_config)
watcher.start()
```

## Stats

```python
print(watcher.stats)
# {
#   "checks": 150,       # poll cycles completed
#   "modifications": 12,  # modification events fired
#   "creations": 3,       # file creation events
#   "deletions": 1,       # file deletion events
#   "size_changes": 8,    # size change events
# }
```

## Freelance: Watch for Bid Responses

```python
watcher = FileWatcher(poll_interval=5.0)
watcher.watch("~/.hermes/logs/gateway.log")

def check_responses(path):
    analyzer = LogAnalyzer()
    analyzer.load_file(path, last_n=50)
    new_responses = analyzer.filter(pattern="bid.*accepted", level="INFO")
    for resp in new_responses:
        notify_accepted_bid(resp)

watcher.on_modified(check_responses)
watcher.start()
```

## Polling Interval Guide

| Interval | CPU Impact | Use Case |
|----------|-----------|----------|
| 0.1s | High | Real-time log tailing |
| 0.5s | Medium | Config hot-reload |
| 2.0s | Low | Directory monitoring (default) |
| 5.0s | Minimal | Infrequent checks |

## Testing

```bash
pytest tests/test_file_watcher.py -v
```

## References

- [watchdog](https://python-watchdog.readthedocs.io/) — when you need kernel-level events
- [inotify](https://man7.org/linux/man-pages/man7/inotify.7.html) — Linux file event system

---

*darkbot-templates v1.8.5 — 30 templates, zero dependencies, 448 tests.*
