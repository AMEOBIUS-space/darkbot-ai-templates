# Cron Scheduler: Periodic Jobs Without Celery-beat

> Part of the [darkbot-templates](https://github.com/AMEOBIUS-space/darkbot-ai-templates) series — zero-dependency production templates.

Need to run a task every 5 minutes? Every hour? The cron scheduler template runs periodic jobs in daemon threads — no celery, no systemd, no external dependencies.

## Usage

```python
from darkbot_templates.templates.cron_scheduler import CronScheduler

scheduler = CronScheduler()

# Schedule a job every 60 seconds
scheduler.every(60, check_health, name="health-check")

# Every 3600 seconds (1 hour)
scheduler.every(3600, cleanup_temp_files, name="cleanup")

# One-shot: run after 300 seconds
scheduler.after(300, send_reminder, name="reminder")

# Start the scheduler (runs in background daemon thread)
scheduler.start()

# Jobs execute automatically on schedule
# ...

# Stop when done
scheduler.stop()
```

## Job Management

```python
job = scheduler.every(30, poll_api, name="poll")

# Pause/resume
job.enabled = False  # skip this cycle
job.enabled = True   # resume

# Limited runs (auto-disable after N executions)
scheduler.every(60, startup_warmup, name="warmup", max_runs=5)

# Check status
for j in scheduler.jobs:
    print(f"  {j.name}: runs={j.runs}, next={j.next_run:.0f}, last_error={j.last_error}")
```

## Error Isolation

Each job runs in a try/except — one job's failure doesn't stop others:

```python
def risky_job():
    raise ConnectionError("API down")

scheduler.every(60, risky_job, name="risky")
scheduler.start()

# Other jobs keep running even if risky_job fails
# Error is captured in job.last_error
```

## Freelance Polling Pattern

```python
from darkbot_templates.templates.cron_scheduler import CronScheduler
from darkbot_templates.templates.rate_limiter import TokenBucketRateLimiter

scheduler = CronScheduler()
limiter = TokenBucketRateLimiter(rate=0.5, capacity=1)

def poll_kwork():
    if not limiter.allow("kwork"):
        return  # rate limited
    jobs = scrape_kwork_projects()
    for job in jobs:
        if is_good_fit(job):
            notify_new_job(job)

def poll_laborx():
    if not limiter.allow("laborx"):
        return
    offers = check_laborx_offers()
    if offers:
        notify_responses(offers)

# Poll every 5 minutes
scheduler.every(300, poll_kwork, name="kwork-poll")
scheduler.every(300, poll_laborx, name="laborx-poll")

scheduler.start()
```

## Health Check Loop

```python
from darkbot_templates.templates.cron_scheduler import CronScheduler
from darkbot_templates.templates.health_checker import HealthChecker

scheduler = CronScheduler()
hc = HealthChecker(timeout=3.0)

def health_probe():
    services = {
        "api": "https://api.example.com/health",
        "db": "https://db.example.com/ping",
    }
    for name, url in services.items():
        result = hc.check(url)
        if result["status"] != "up":
            send_alert(f"{name} is {result['status']}")

scheduler.every(60, health_probe, name="health")
scheduler.start()
```

## Thread Safety

Jobs run in the scheduler's daemon thread (sequential, not parallel). For parallel job execution, combine with `TaskQueue`:

```python
from darkbot_templates.templates.task_queue import TaskQueue

queue = TaskQueue(max_workers=4)
queue.start()

scheduler = CronScheduler()

def enqueue_batch():
    for item in get_work_items():
        queue.enqueue(process_item, args=(item,))

scheduler.every(120, enqueue_batch, name="batch")
scheduler.start()
```

## Testing

```bash
pytest tests/test_cron_scheduler.py -v
```

## References

- [APScheduler](https://apscheduler.readthedocs.io/) — fuller-featured alternative
- [cron expression format](https://en.wikipedia.org/wiki/Cron)

---

*darkbot-templates v1.8.5 — 30 templates, zero dependencies, 448 tests.*
