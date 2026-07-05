import sys, os, time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from task_queue import TaskQueue, Task, TaskStatus


def test_submit_task():
    q = TaskQueue(num_workers=0)
    task_id = q.submit("echo", {"msg": "hello"}, priority=5)
    assert task_id.startswith("task_")
    assert len(q._heap) == 1


def test_priority_ordering():
    import heapq as hq
    q = TaskQueue(num_workers=0)
    q.submit("low", priority=10)
    q.submit("high", priority=1)
    q.submit("mid", priority=5)
    # Pop in priority order: high(1) -> mid(5) -> low(10)
    first = hq.heappop(q._heap)
    assert first.priority == 1
    second = hq.heappop(q._heap)
    assert second.priority == 5
    assert len(q._heap) == 1


def test_register_handler():
    q = TaskQueue()
    q.register_handler("echo", lambda p: p["msg"])
    assert "echo" in q.handlers


def test_worker_completes_task():
    q = TaskQueue(num_workers=1)
    q.register_handler("double", lambda p: p["x"] * 2)
    q.start()
    task_id = q.submit("double", {"x": 21})
    time.sleep(0.5)
    q.stop()
    task = q.get_task(task_id)
    assert task is not None
    assert task.status == TaskStatus.COMPLETED
    assert task.result == 42


def test_worker_retries():
    attempts = []
    q = TaskQueue(num_workers=1)
    
    def flaky_handler(payload):
        attempts.append(1)
        if len(attempts) < 2:
            raise Exception("Temporary failure")
        return "success"
    
    q.register_handler("flaky", flaky_handler)
    q.start()
    q.submit("flaky", {}, max_retries=3, retry_delay=0.01)
    time.sleep(1)
    q.stop()
    assert len(attempts) >= 2
    assert len(q.completed) >= 1


def test_handler_not_found():
    q = TaskQueue(num_workers=1)
    q.start()
    q.submit("unknown_task", {})
    time.sleep(0.3)
    q.stop()
    assert len(q.failed) == 1
    assert "No handler" in q.failed[0].error


def test_cancel_task():
    q = TaskQueue(num_workers=0)
    task_id = q.submit("cancel_me", {})
    assert q.cancel(task_id)
    assert len(q._heap) == 0


def test_stats():
    q = TaskQueue(num_workers=2)
    q.register_handler("echo", lambda p: p.get("x", 1))
    q.start()
    q.submit("echo", {"x": 1})
    q.submit("echo", {"x": 2})
    time.sleep(0.5)
    q.stop()
    stats = q.stats()
    assert stats["completed"] == 2
    assert stats["workers"] == 2


def test_max_retries_exceeded():
    q = TaskQueue(num_workers=1)
    q.register_handler("always_fail", lambda p: (_ for _ in ()).throw(Exception("Permanent")))
    q.start()
    q.submit("always_fail", {}, max_retries=2, retry_delay=0.01)
    time.sleep(1)
    q.stop()
    assert len(q.failed) == 1
    assert "Permanent" in q.failed[0].error


def test_multiple_workers():
    q = TaskQueue(num_workers=3)
    q.register_handler("echo", lambda p: p["x"])
    q.start()
    for i in range(6):
        q.submit("echo", {"x": i})
    time.sleep(0.5)
    q.stop()
    assert len(q.completed) == 6


def test_wait_for_completion():
    q = TaskQueue(num_workers=1)
    q.register_handler("fast", lambda p: "ok")
    q.start()
    q.submit("fast", {})
    result = q.wait_for_completion(timeout=2)
    q.stop()
    assert result is True


def test_get_task_not_found():
    q = TaskQueue()
    assert q.get_task("nonexistent") is None


def test_task_status_completed():
    q = TaskQueue(num_workers=1)
    q.register_handler("echo", lambda p: "done")
    q.start()
    task_id = q.submit("echo", {})
    time.sleep(0.3)
    q.stop()
    task = q.get_task(task_id)
    assert task.status == TaskStatus.COMPLETED
