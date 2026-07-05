# Cron Job Scheduler

> Parse cron expressions, calculate next runs, and manage scheduled jobs

## Features

- Full 5-field cron expression parser (*, */n, a-b, a,b,c, month/day names)
- Next-run calculation (searches up to 366 days ahead)
- Job management (add, remove, enable, disable)
- Manual job triggering
- Background scheduler loop
- Error tracking per job
- Run count tracking
- Job listing and statistics

## Quick Start

```python
from scheduler import CronScheduler

sched = CronScheduler()
sched.add("daily_report", "Daily Report", "0 9 * * *", handler=send_report)
sched.add("hourly_check", "Hourly Check", "0 * * * *", handler=health_check)
sched.start()
```

## Tests

```bash
python -m pytest tests/ -v
```

## License

MIT
