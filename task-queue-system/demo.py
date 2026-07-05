#!/usr/bin/env python3
"""Demo: Task Queue System."""
import sys, os, json, time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))
from task_queue import TaskQueue, TaskStatus

q = TaskQueue(num_workers=2)
q.register_handler("fetch", lambda p: {"url": p["url"], "status": 200, "bytes": 1024})
q.register_handler("process", lambda p: {"input": p["data"], "output": p["data"].upper()})
q.register_handler("notify", lambda p: f"Sent to {p['channel']}")

q.start()

# Submit tasks with different priorities
q.submit("fetch", {"url": "https://api.example.com"}, priority=1)
q.submit("process", {"data": "hello world"}, priority=5)
q.submit("notify", {"channel": "telegram"}, priority=10)
q.submit("fetch", {"url": "https://db.example.com"}, priority=2)

time.sleep(1)
q.stop()

print("=== Completed Tasks ===")
for task in q.completed:
    print(f"  {task.id} | {task.name} | priority={task.priority} | result={task.result}")

print(f"\nStats: {json.dumps(q.stats(), indent=2)}")
