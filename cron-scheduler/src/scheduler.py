"""Cron Job Scheduler — parse cron expressions, calculate next runs, manage jobs."""
import re
import time
import json
import threading
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass, asdict, field
from datetime import datetime, timedelta
from pathlib import Path


@dataclass
class CronJob:
    id: str
    name: str
    cron_expr: str
    handler: Optional[Callable] = None
    enabled: bool = True
    last_run: str = ""
    next_run: str = ""
    run_count: int = 0
    error_count: int = 0
    last_error: str = ""
    timeout: int = 300  # seconds
    metadata: Dict = field(default_factory=dict)


class CronExpression:
    """Parse and evaluate cron expressions (5-field: min hour day month weekday)."""

    FIELD_RANGES = {
        "minute": (0, 59),
        "hour": (0, 23),
        "day": (1, 31),
        "month": (1, 12),
        "weekday": (0, 6),  # 0=Sunday
    }

    MONTH_NAMES = {"jan": 1, "feb": 2, "mar": 3, "apr": 4, "may": 5, "jun": 6,
                   "jul": 7, "aug": 8, "sep": 9, "oct": 10, "nov": 11, "dec": 12}
    DAY_NAMES = {"sun": 0, "mon": 1, "tue": 2, "wed": 3, "thu": 4, "fri": 5, "sat": 6}

    @classmethod
    def parse(cls, expr: str) -> Dict[str, List[int]]:
        """Parse a 5-field cron expression into sets of matching values."""
        fields = expr.strip().split()
        if len(fields) != 5:
            raise ValueError(f"Expected 5 fields, got {len(fields)}: '{expr}'")

        field_names = ["minute", "hour", "day", "month", "weekday"]
        result = {}
        for i, fname in enumerate(field_names):
            result[fname] = cls._parse_field(fields[i], cls.FIELD_RANGES[fname], fname)
        return result

    @classmethod
    def _parse_field(cls, field: str, value_range: tuple, fname: str) -> List[int]:
        """Parse a single cron field (supports *, */n, a-b, a,b,c, names)."""
        min_val, max_val = value_range
        values = set()

        for part in field.split(","):
            part = part.strip().lower()

            # Handle names
            if fname == "month":
                for name, num in cls.MONTH_NAMES.items():
                    part = part.replace(name, str(num))
            elif fname == "weekday":
                for name, num in cls.DAY_NAMES.items():
                    part = part.replace(name, str(num))

            if part == "*":
                values.update(range(min_val, max_val + 1))
            elif "/" in part:
                base, step = part.split("/")
                step = int(step)
                if base == "*":
                    start, end = min_val, max_val
                elif "-" in base:
                    start, end = map(int, base.split("-"))
                else:
                    start = int(base)
                    end = max_val
                values.update(range(start, end + 1, step))
            elif "-" in part:
                start, end = map(int, part.split("-"))
                values.update(range(start, end + 1))
            else:
                values.add(int(part))

        return sorted(v for v in values if min_val <= v <= max_val)

    @classmethod
    def matches(cls, dt: datetime, parsed: Dict[str, List[int]]) -> bool:
        """Check if a datetime matches the parsed cron expression."""
        return (dt.minute in parsed["minute"] and
                dt.hour in parsed["hour"] and
                dt.day in parsed["day"] and
                dt.month in parsed["month"] and
                dt.weekday() % 7 in parsed["weekday"])  # Python weekday: 0=Monday, cron: 0=Sunday

    @classmethod
    def next_run(cls, expr: str, after: datetime = None) -> datetime:
        """Calculate the next time this expression will match."""
        parsed = cls.parse(expr)
        after = after or datetime.now()
        # Start from next minute
        candidate = after.replace(second=0, microsecond=0) + timedelta(minutes=1)

        # Search up to 366 days ahead
        max_iter = 366 * 24 * 60
        for _ in range(max_iter):
            if cls.matches(candidate, parsed):
                return candidate
            candidate += timedelta(minutes=1)

        raise ValueError(f"No matching time found within 366 days for '{expr}'")


class CronScheduler:
    """Schedule and execute jobs based on cron expressions."""

    def __init__(self):
        self.jobs: Dict[str, CronJob] = {}
        self._lock = threading.Lock()
        self._running = False
        self._thread = None

    def add(self, job_id: str, name: str, cron_expr: str,
            handler: Callable = None, timeout: int = 300) -> CronJob:
        """Add a cron job."""
        # Validate expression
        CronExpression.parse(cron_expr)
        next_dt = CronExpression.next_run(cron_expr)
        job = CronJob(
            id=job_id, name=name, cron_expr=cron_expr,
            handler=handler, timeout=timeout,
            next_run=next_dt.isoformat(),
        )
        with self._lock:
            self.jobs[job_id] = job
        return job

    def remove(self, job_id: str) -> bool:
        with self._lock:
            if job_id in self.jobs:
                del self.jobs[job_id]
                return True
            return False

    def enable(self, job_id: str) -> bool:
        with self._lock:
            if job_id in self.jobs:
                self.jobs[job_id].enabled = True
                return True
            return False

    def disable(self, job_id: str) -> bool:
        with self._lock:
            if job_id in self.jobs:
                self.jobs[job_id].enabled = False
                return True
            return False

    def run_job(self, job_id: str) -> bool:
        """Manually trigger a job."""
        with self._lock:
            job = self.jobs.get(job_id)
        if not job:
            return False
        try:
            if job.handler:
                job.handler()
            job.run_count += 1
            job.last_run = datetime.now().isoformat()
            job.next_run = CronExpression.next_run(job.cron_expr).isoformat()
            return True
        except Exception as e:
            job.error_count += 1
            job.last_error = str(e)
            return False

    def start(self):
        """Start the scheduler loop."""
        self._running = True
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()

    def stop(self):
        self._running = False
        if self._thread:
            self._thread.join(timeout=5)

    def _loop(self):
        while self._running:
            now = datetime.now()
            with self._lock:
                due_jobs = [j for j in self.jobs.values()
                           if j.enabled and j.next_run and
                           datetime.fromisoformat(j.next_run) <= now]
            for job in due_jobs:
                self.run_job(job.id)
            time.sleep(1)

    def list_jobs(self) -> List[Dict]:
        with self._lock:
            return [
                {"id": j.id, "name": j.name, "cron": j.cron_expr,
                 "enabled": j.enabled, "next_run": j.next_run,
                 "run_count": j.run_count, "error_count": j.error_count}
                for j in self.jobs.values()
            ]

    def stats(self) -> Dict:
        return {
            "total_jobs": len(self.jobs),
            "enabled": sum(1 for j in self.jobs.values() if j.enabled),
            "disabled": sum(1 for j in self.jobs.values() if not j.enabled),
            "total_runs": sum(j.run_count for j in self.jobs.values()),
            "total_errors": sum(j.error_count for j in self.jobs.values()),
        }
