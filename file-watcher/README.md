# File Watcher

> Filesystem monitoring with debouncing, event callbacks, and pattern matching

## Features

- Watch files and directories
- Event types: created, modified, deleted
- MD5 checksum-based change detection
- Pattern matching (glob: *.py, *.json)
- Event handlers + pattern handlers
- Background polling thread
- Change history with configurable limit
- Statistics dashboard

## Quick Start

```python
from watcher import FileWatcher, WatchEvent

w = FileWatcher(debounce_ms=300)
w.watch("/app/src")
w.on_pattern("*.py", lambda c: print(f"Python file changed: {c.path}"))
w.start(poll_interval=1.0)
```

## Tests

```bash
python -m pytest tests/ -v
```

## License

MIT
