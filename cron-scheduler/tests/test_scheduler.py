import sys, os, time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from scheduler import CronExpression, CronScheduler, CronJob
from datetime import datetime


def test_parse_star():
    parsed = CronExpression.parse("* * * * *")
    assert 0 in parsed["minute"]
    assert 23 in parsed["hour"]
    assert 31 in parsed["day"]


def test_parse_specific():
    parsed = CronExpression.parse("30 9 * * *")
    assert parsed["minute"] == [30]
    assert parsed["hour"] == [9]


def test_parse_step():
    parsed = CronExpression.parse("*/15 * * * *")
    assert 0 in parsed["minute"]
    assert 15 in parsed["minute"]
    assert 30 in parsed["minute"]
    assert 45 in parsed["minute"]


def test_parse_range():
    parsed = CronExpression.parse("0 9-17 * * *")
    assert 9 in parsed["hour"]
    assert 17 in parsed["hour"]
    assert 8 not in parsed["hour"]


def test_parse_list():
    parsed = CronExpression.parse("0 9,12,18 * * *")
    assert parsed["hour"] == [9, 12, 18]


def test_parse_names():
    parsed = CronExpression.parse("0 0 * * mon")
    assert 1 in parsed["weekday"]  # Monday = 1 in cron


def test_parse_invalid():
    try:
        CronExpression.parse("invalid")
        assert False, "Should raise"
    except ValueError:
        pass


def test_next_run_every_minute():
    dt = datetime(2026, 7, 5, 12, 0, 0)
    next_dt = CronExpression.next_run("* * * * *", after=dt)
    assert next_dt == datetime(2026, 7, 5, 12, 1, 0)


def test_next_run_daily():
    dt = datetime(2026, 7, 5, 12, 0, 0)
    next_dt = CronExpression.next_run("0 9 * * *", after=dt)
    assert next_dt.hour == 9
    assert next_dt.day == 6  # Next day


def test_next_run_hourly():
    dt = datetime(2026, 7, 5, 12, 30, 0)
    next_dt = CronExpression.next_run("0 * * * *", after=dt)
    assert next_dt.hour == 13
    assert next_dt.minute == 0


def test_add_job():
    sched = CronScheduler()
    job = sched.add("job1", "Daily Report", "0 9 * * *")
    assert job.id == "job1"
    assert job.cron_expr == "0 9 * * *"
    assert job.next_run  # Should have next_run calculated


def test_remove_job():
    sched = CronScheduler()
    sched.add("job1", "Test", "0 9 * * *")
    assert sched.remove("job1") is True
    assert sched.remove("job1") is False


def test_enable_disable():
    sched = CronScheduler()
    sched.add("job1", "Test", "0 9 * * *")
    assert sched.disable("job1") is True
    assert sched.jobs["job1"].enabled is False
    assert sched.enable("job1") is True
    assert sched.jobs["job1"].enabled is True


def test_run_job():
    sched = CronScheduler()
    results = []
    sched.add("job1", "Test", "0 9 * * *", handler=lambda: results.append(1))
    assert sched.run_job("job1") is True
    assert len(results) == 1
    assert sched.jobs["job1"].run_count == 1


def test_run_job_error():
    sched = CronScheduler()
    def bad_handler():
        raise Exception("Test error")
    sched.add("job1", "Test", "0 9 * * *", handler=bad_handler)
    sched.run_job("job1")
    assert sched.jobs["job1"].error_count == 1
    assert "Test error" in sched.jobs["job1"].last_error


def test_run_nonexistent():
    sched = CronScheduler()
    assert sched.run_job("nonexistent") is False


def test_list_jobs():
    sched = CronScheduler()
    sched.add("job1", "Daily", "0 9 * * *")
    sched.add("job2", "Hourly", "0 * * * *")
    jobs = sched.list_jobs()
    assert len(jobs) == 2
    assert jobs[0]["cron"] == "0 9 * * *"


def test_stats():
    sched = CronScheduler()
    sched.add("job1", "A", "0 9 * * *")
    sched.add("job2", "B", "0 * * * *")
    sched.disable("job2")
    sched.run_job("job1")
    stats = sched.stats()
    assert stats["total_jobs"] == 2
    assert stats["enabled"] == 1
    assert stats["total_runs"] == 1


def test_start_stop():
    sched = CronScheduler()
    sched.start()
    time.sleep(0.2)
    assert sched._running is True
    sched.stop()
    assert sched._running is False
