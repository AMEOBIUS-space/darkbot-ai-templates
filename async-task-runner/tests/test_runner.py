import sys, os, asyncio, time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from runner import AsyncTaskRunner, AsyncTask, TaskState


def test_submit():
    runner = AsyncTaskRunner()
    tid = runner.submit("test", lambda: asyncio.sleep(0.01))
    assert tid.startswith("task_")
    assert runner.get_task(tid).state == TaskState.PENDING

def test_run_single_success():
    async def run():
        runner = AsyncTaskRunner()
        tid = runner.submit("double", lambda: asyncio.coroutine(lambda: 42)())
        # Use a proper async function
        tid = runner.submit("compute", lambda: _async_42())
        await runner.run_single(tid)
        task = runner.get_task(tid)
        assert task.state == TaskState.COMPLETED
        assert task.result == 42
    asyncio.run(run())

async def _async_42():
    return 42

def test_run_single_with_sleep():
    async def run():
        runner = AsyncTaskRunner()
        async def slow():
            await asyncio.sleep(0.05)
            return "done"
        tid = runner.submit("slow", slow)
        await runner.run_single(tid)
        task = runner.get_task(tid)
        assert task.state == TaskState.COMPLETED
        assert task.result == "done"
        assert task.duration >= 0.04
    asyncio.run(run())

def test_run_single_failure():
    async def run():
        runner = AsyncTaskRunner()
        async def fail():
            raise ValueError("boom")
        tid = runner.submit("fail", fail)
        await runner.run_single(tid)
        task = runner.get_task(tid)
        assert task.state == TaskState.FAILED
        assert "boom" in task.error
    asyncio.run(run())

def test_timeout():
    async def run():
        runner = AsyncTaskRunner(default_timeout=0.05)
        async def slow():
            await asyncio.sleep(1.0)
            return "too slow"
        tid = runner.submit("slow", slow)
        await runner.run_single(tid)
        task = runner.get_task(tid)
        assert task.state == TaskState.TIMEOUT
    asyncio.run(run())

def test_run_all():
    async def run():
        runner = AsyncTaskRunner(max_concurrency=5)
        async def quick(x):
            await asyncio.sleep(0.01)
            return x
        for i in range(5):
            runner.submit(f"task_{i}", lambda i=i: quick(i))
        results = await runner.run_all()
        assert len(results) == 5
        for task in results.values():
            assert task.state == TaskState.COMPLETED
    asyncio.run(run())

def test_run_batch():
    async def run():
        runner = AsyncTaskRunner()
        async def echo(x):
            return x
        factories = [("t1", lambda: echo(1)), ("t2", lambda: echo(2)), ("t3", lambda: echo(3))]
        results = await runner.run_batch(factories)
        assert len(results) == 3
    asyncio.run(run())

def test_cancel():
    runner = AsyncTaskRunner()
    tid = runner.submit("test", lambda: asyncio.sleep(1))
    assert runner.cancel(tid) is True
    assert runner.get_task(tid).state == TaskState.CANCELLED

def test_cancel_nonexistent():
    runner = AsyncTaskRunner()
    assert runner.cancel("nonexistent") is False

def test_get_results():
    async def run():
        runner = AsyncTaskRunner()
        async def val(x):
            return x
        t1 = runner.submit("a", lambda: val(10))
        t2 = runner.submit("b", lambda: val(20))
        await runner.run_all()
        results = runner.get_results()
        assert len(results) == 2
    asyncio.run(run())

def test_get_errors():
    async def run():
        runner = AsyncTaskRunner()
        async def ok():
            return 1
        async def bad():
            raise Exception("error")
        runner.submit("ok", ok)
        runner.submit("bad", bad)
        await runner.run_all()
        errors = runner.get_errors()
        assert "bad" in errors or any(tid for tid in errors if runner.get_task(tid).name == "bad")
    asyncio.run(run())

def test_list_tasks():
    async def run():
        runner = AsyncTaskRunner()
        async def x():
            return 1
        runner.submit("a", x)
        runner.submit("b", x)
        await runner.run_all()
        tasks = runner.list_tasks()
        assert len(tasks) == 2
    asyncio.run(run())

def test_stats():
    async def run():
        runner = AsyncTaskRunner(max_concurrency=3)
        async def x():
            await asyncio.sleep(0.01)
            return 1
        runner.submit("a", x)
        runner.submit("b", x)
        await runner.run_all()
        stats = runner.stats()
        assert stats["total"] == 2
        assert stats["completed"] == 2
        assert stats["max_concurrency"] == 3
    asyncio.run(run())

def test_progress_update():
    runner = AsyncTaskRunner()
    tid = runner.submit("test", lambda: asyncio.sleep(1))
    runner.update_progress(tid, 0.5)
    assert runner.get_task(tid).progress == 0.5

def test_progress_callback():
    runner = AsyncTaskRunner()
    progress_log = []
    tid = runner.submit("test", lambda: asyncio.sleep(1))
    runner.on_progress(tid, lambda p: progress_log.append(p))
    runner.update_progress(tid, 0.3)
    runner.update_progress(tid, 0.7)
    assert progress_log == [0.3, 0.7]

def test_concurrency_control():
    async def run():
        runner = AsyncTaskRunner(max_concurrency=2)
        concurrent = 0
        max_concurrent = 0
        async def track():
            nonlocal concurrent, max_concurrent
            concurrent += 1
            max_concurrent = max(max_concurrent, concurrent)
            await asyncio.sleep(0.05)
            concurrent -= 1
            return "ok"
        for i in range(6):
            runner.submit(f"t{i}", track)
        await runner.run_all()
        assert max_concurrent <= 2
    asyncio.run(run())

def test_metadata():
    runner = AsyncTaskRunner()
    tid = runner.submit("test", lambda: asyncio.sleep(0.01), metadata={"priority": "high"})
    assert runner.get_task(tid).metadata["priority"] == "high"
