# Task Queue System

> Priority-based async task queue with retries and multi-worker support

## Features

- Priority queue (lower number = higher priority)
- Configurable worker threads
- Retry with exponential backoff (max_retries + retry_delay)
- Handler registry by task name
- Task cancellation
- Task status tracking (pending, running, completed, failed, retrying, cancelled)
- Wait for completion
- Statistics dashboard

## Quick Start

```python
from task_queue import TaskQueue

q = TaskQueue(num_workers=3)
q.register_handler("send_email", lambda p: send_smtp(p))
q.start()
q.submit("send_email", {"to": "user@example.com"}, priority=1)
```

## Tests

```bash
python -m pytest tests/ -v
```

## License

MIT
