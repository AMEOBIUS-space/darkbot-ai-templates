# Async Task Runner

> Async/await task execution with concurrency control, timeout, and progress tracking

## Features

- Async task submission and execution
- Concurrency control (Semaphore-based max_concurrency)
- Timeout per task (asyncio.wait_for)
- Progress tracking (0.0-1.0) with callbacks
- Task states: pending, running, completed, failed, cancelled, timeout
- Batch execution (submit + run in one call)
- Run all tasks with asyncio.gather
- Task cancellation
- Results and errors collection
- Metadata support
- Statistics dashboard

## Quick Start

```python
import asyncio
from runner import AsyncTaskRunner

async def main():
    runner = AsyncTaskRunner(max_concurrency=5, default_timeout=10)
    
    async def fetch(url):
        await asyncio.sleep(0.1)
        return f"Response from {url}"
    
    tid = runner.submit("fetch_api", lambda: fetch("https://api.example.com"))
    await runner.run_single(tid)
    
    print(runner.get_task(tid).result)

asyncio.run(main())
```

## Tests

```bash
python -m pytest tests/ -v
```

## License

MIT
