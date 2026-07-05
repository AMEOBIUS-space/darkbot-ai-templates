"""Task Queue System — async job processing with priorities, retries, and workers."""
import time
import json
import threading
import heapq
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass, asdict, field
from datetime import datetime
from enum import Enum
from queue import Queue, Empty


class TaskStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRYING = "retrying"
    CANCELLED = "cancelled"


@dataclass(order=True)
class Task:
    priority: int  # Lower = higher priority
    created_at: float
    id: str
    name: str
    payload: Dict = field(default_factory=dict, compare=False)
    status: TaskStatus = field(default=TaskStatus.PENDING, compare=False)
    retries: int = field(default=0, compare=False)
    max_retries: int = field(default=3, compare=False)
    retry_delay: float = field(default=1.0, compare=False)
    result: Any = field(default=None, compare=False)
    error: str = field(default="", compare=False)
    started_at: str = field(default="", compare=False)
    completed_at: str = field(default="", compare=False)
    worker_id: str = field(default="", compare=False)


class TaskQueue:
    """Priority-based task queue with retry support and worker threads."""

    def __init__(self, num_workers: int = 1):
        self.num_workers = num_workers
        self._heap: List[Task] = []
        self._lock = threading.Lock()
        self._condition = threading.Condition(self._lock)
        self.handlers: Dict[str, Callable] = {}
        self.completed: List[Task] = []
        self.failed: List[Task] = []
        self._workers: List[threading.Thread] = []
        self._running = False
        self._counter = 0

    def register_handler(self, task_name: str, handler: Callable):
        self.handlers[task_name] = handler

    def submit(self, task_name: str, payload: Dict = None, priority: int = 10,
               max_retries: int = 3, retry_delay: float = 1.0) -> str:
        """Submit a task to the queue. Returns task ID."""
        with self._lock:
            self._counter += 1
            task_id = f"task_{self._counter}"
            task = Task(
                priority=priority,
                created_at=time.time(),
                id=task_id,
                name=task_name,
                payload=payload or {},
                max_retries=max_retries,
                retry_delay=retry_delay,
            )
            heapq.heappush(self._heap, task)
            self._condition.notify()
            return task_id

    def cancel(self, task_id: str) -> bool:
        """Cancel a pending task."""
        with self._lock:
            for i, task in enumerate(self._heap):
                if task.id == task_id and task.status == TaskStatus.PENDING:
                    task.status = TaskStatus.CANCELLED
                    self._heap.pop(i)
                    heapq.heapify(self._heap)
                    return True
            return False

    def start(self):
        """Start worker threads."""
        self._running = True
        for i in range(self.num_workers):
            worker = threading.Thread(target=self._worker_loop, args=(f"worker_{i}",), daemon=True)
            worker.start()
            self._workers.append(worker)

    def stop(self):
        """Stop all workers."""
        self._running = False
        with self._lock:
            self._condition.notify_all()

    def _worker_loop(self, worker_id: str):
        while self._running:
            with self._lock:
                while not self._heap and self._running:
                    self._condition.wait(timeout=1)
                if not self._running:
                    break
                task = heapq.heappop(self._heap)
                task.status = TaskStatus.RUNNING
                task.started_at = datetime.now().isoformat()
                task.worker_id = worker_id

            # Execute outside lock
            handler = self.handlers.get(task.name)
            if not handler:
                task.status = TaskStatus.FAILED
                task.error = f"No handler for '{task.name}'"
                self.failed.append(task)
                continue

            try:
                task.result = handler(task.payload)
                task.status = TaskStatus.COMPLETED
                task.completed_at = datetime.now().isoformat()
                self.completed.append(task)
            except Exception as e:
                task.retries += 1
                if task.retries <= task.max_retries:
                    task.status = TaskStatus.RETRYING
                    time.sleep(task.retry_delay * task.retries)
                    task.status = TaskStatus.PENDING
                    with self._lock:
                        heapq.heappush(self._heap, task)
                        self._condition.notify()
                else:
                    task.status = TaskStatus.FAILED
                    task.error = str(e)
                    self.failed.append(task)

    def wait_for_completion(self, timeout: float = 10) -> bool:
        """Wait for all tasks to complete. Returns True if all done."""
        deadline = time.time() + timeout
        while time.time() < deadline:
            with self._lock:
                if not self._heap:
                    return True
            time.sleep(0.1)
        return False

    def get_task(self, task_id: str) -> Optional[Task]:
        """Get a task by ID from completed/failed lists."""
        for task in self.completed + self.failed:
            if task.id == task_id:
                return task
        return None

    def stats(self) -> Dict:
        with self._lock:
            pending = len(self._heap)
        return {
            "pending": pending,
            "completed": len(self.completed),
            "failed": len(self.failed),
            "workers": self.num_workers,
            "running": self._running,
        }
