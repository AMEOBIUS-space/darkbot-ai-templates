# Task Queue: Priority Workers Without Celery

> Part of the [darkbot-templates](https://github.com/AMEOBIUS-space/darkbot-ai-templates) series — zero-dependency production templates.

Celery is powerful but needs Redis/RabbitMQ. For background jobs within a single process — email sending, file processing, bid submission — this template gives you a priority task queue with a worker pool.

## Usage

```python
from darkbot_templates.templates.task_queue import TaskQueue

queue = TaskQueue(max_workers=4)

# Enqueue tasks (priority 0=highest)
queue.enqueue(send_email, args=("client@example.com",), priority=0)
queue.enqueue(process_file, args=("report.csv",), priority=5)
queue.enqueue(cleanup_temp, priority=10)

# Start workers
queue.start()

# Wait for all tasks to complete
queue.join()

# Stop workers
queue.stop()
```

## Priority Ordering

Lower number = higher priority:

```python
queue.enqueue(critical_alert, priority=0)    # runs first
queue.enqueue(send_report, priority=5)       # runs second
queue.enqueue(cleanup, priority=10)          # runs last
```

## Task Status

```python
task = queue.enqueue(long_running_task, args=(42,))

task.status       # "queued" | "running" | "completed" | "failed"
task.result       # return value (after completion)
task.error        # exception message (if failed)
task.started_at   # timestamp
task.completed_at # timestamp
task.duration     # seconds (after completion)
```

## Worker Pool

```python
# 4 worker threads process tasks concurrently
queue = TaskQueue(max_workers=4)
queue.start()

# Tasks are distributed across workers
for job_id in range(100):
    queue.enqueue(process_job, args=(job_id,))

queue.join()  # blocks until all 100 done
```

## Task Cancellation

```python
task = queue.enqueue(long_task, args=("big_file.dat",))

# Cancel if still queued
if task.status == "queued":
    queue.cancel(task.id)

# Can't cancel a running task (it will complete)
```

## Error Handling

```python
def risky_task(data):
    if not data:
        raise ValueError("Empty data")
    return transform(data)

task = queue.enqueue(risky_task, args=("",))

queue.join()

if task.status == "failed":
    print(f"Task failed: {task.error}")
    # → "Task failed: Empty data"
```

## Freelance Bid Scheduler

```python
from darkbot_templates.templates.task_queue import TaskQueue
from darkbot_templates.templates.rate_limiter import TokenBucketRateLimiter

queue = TaskQueue(max_workers=2)
limiter = TokenBucketRateLimiter(rate=0.5, capacity=3)  # 1 bid per 2 seconds

def submit_bid(platform, job_id, amount):
    while not limiter.allow(platform):
        time.sleep(limiter.wait_time(platform))
    return api.submit_bid(platform, job_id, amount)

queue.start()

# Queue bids across platforms
for job in scrape_kwork_jobs():
    queue.enqueue(submit_bid, args=("kwork", job["id"], job["bid_amount"]), priority=job["priority"])

for job in scrape_laborx_jobs():
    queue.enqueue(submit_bid, args=("laborx", job["id"], job["bid_amount"]), priority=job["priority"])

queue.join()
print("All bids submitted!")
```

## File Processing Pipeline

```python
queue = TaskQueue(max_workers=4)
queue.start()

# Stage 1: Download
for url in download_urls:
    queue.enqueue(download_file, args=(url,), priority=0)

queue.join()

# Stage 2: Process (after all downloads complete)
for path in downloaded_files:
    queue.enqueue(process_file, args=(path,), priority=5)

queue.join()

# Stage 3: Upload results
for result in processed_files:
    queue.enqueue(upload_result, args=(result,), priority=10)

queue.join()
```

## Statistics

```python
stats = queue.stats
# {
#   "queued": 5,
#   "running": 2,
#   "completed": 150,
#   "failed": 3,
#   "total_workers": 4,
#   "active_workers": 2,
# }
```

## Combining with Retry Queue

```python
from darkbot_templates.templates.retry_queue import RetryQueue

queue = TaskQueue(max_workers=4)
retry = RetryQueue()

def fetch_with_retry(url):
    try:
        result = http_get(url)
        return result
    except Exception:
        # Move to retry queue for later
        retry.enqueue(RetryItem(func=fetch_with_retry, args=(url,)))
        return None

queue.start()
queue.enqueue(fetch_with_retry, args=("https://flaky-api.com/data",))
```

## Testing

```bash
pytest tests/test_task_queue.py -v
```

## References

- [Python concurrent.futures](https://docs.python.org/3/library/concurrent.futures.html) — the stdlib basis
- [Celery](https://docs.celeryq.dev/) — when you need distributed queues

---

*darkbot-templates v1.8.5 — 30 templates, zero dependencies, 448 tests.*
