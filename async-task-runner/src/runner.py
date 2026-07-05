"""Async Task Runner — async/await task execution with concurrency and progress."""
import asyncio
import time
from typing import Dict, List, Optional, Callable, Any, Tuple, Set
from dataclasses import dataclass, asdict, field
from datetime import datetime
from enum import Enum


class TaskState(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMEOUT = "timeout"


@dataclass
class AsyncTask:
    id: str
    name: str
    coro: Optional[Callable] = None
    state: TaskState = TaskState.PENDING
    result: Any = None
    error: str = ""
    started_at: str = ""
    completed_at: str = ""
    duration: float = 0.0
    timeout: float = 0.0
    progress: float = 0.0
    metadata: Dict = field(default_factory=dict)


class AsyncTaskRunner:
    """Run async tasks with concurrency control, timeout, and progress tracking."""

    def __init__(self, max_concurrency: int = 10, default_timeout: float = 30.0):
        self.max_concurrency = max_concurrency
        self.default_timeout = default_timeout
        self._tasks: Dict[str, AsyncTask] = {}
        self._semaphore: Optional[asyncio.Semaphore] = None
        self._counter = 0
        self._progress_callbacks: Dict[str, Callable] = {}

    def submit(self, name: str, coro_factory: Callable, timeout: float = None,
               metadata: Dict = None) -> str:
        """Submit a task. Returns task ID."""
        self._counter += 1
        task_id = f"task_{self._counter}"
        task = AsyncTask(
            id=task_id, name=name, coro=coro_factory,
            timeout=timeout or self.default_timeout,
            metadata=metadata or {},
        )
        self._tasks[task_id] = task
        return task_id

    def on_progress(self, task_id: str, callback: Callable):
        """Register progress callback for a task."""
        self._progress_callbacks[task_id] = callback

    def update_progress(self, task_id: str, progress: float):
        """Update task progress (0.0 to 1.0)."""
        task = self._tasks.get(task_id)
        if task:
            task.progress = max(0.0, min(1.0, progress))
            callback = self._progress_callbacks.get(task_id)
            if callback:
                callback(task.progress)

    async def run_single(self, task_id: str) -> AsyncTask:
        """Run a single task."""
        task = self._tasks.get(task_id)
        if not task:
            return AsyncTask(id=task_id, name="unknown", state=TaskState.FAILED, error="Task not found")

        task.state = TaskState.RUNNING
        task.started_at = datetime.now().isoformat()
        start = time.time()

        try:
            if task.timeout > 0:
                result = await asyncio.wait_for(task.coro(), timeout=task.timeout)
            else:
                result = await task.coro()
            task.result = result
            task.state = TaskState.COMPLETED
            task.progress = 1.0
        except asyncio.TimeoutError:
            task.state = TaskState.TIMEOUT
            task.error = f"Timed out after {task.timeout}s"
        except asyncio.CancelledError:
            task.state = TaskState.CANCELLED
        except Exception as e:
            task.state = TaskState.FAILED
            task.error = str(e)

        task.duration = time.time() - start
        task.completed_at = datetime.now().isoformat()
        return task

    async def run_all(self, task_ids: List[str] = None) -> Dict[str, AsyncTask]:
        """Run multiple tasks with concurrency control."""
        self._semaphore = asyncio.Semaphore(self.max_concurrency)
        ids = task_ids or list(self._tasks.keys())

        async def bounded_run(tid):
            async with self._semaphore:
                return await self.run_single(tid)

        results = await asyncio.gather(*[bounded_run(tid) for tid in ids], return_exceptions=True)
        return {tid: r for tid, r in zip(ids, results) if not isinstance(r, Exception)}

    async def run_batch(self, coro_factories: List[Tuple[str, Callable]],
                        timeout: float = None) -> Dict[str, AsyncTask]:
        """Submit and run a batch of tasks."""
        task_ids = []
        for name, factory in coro_factories:
            tid = self.submit(name, factory, timeout=timeout)
            task_ids.append(tid)
        return await self.run_all(task_ids)

    def cancel(self, task_id: str) -> bool:
        """Cancel a pending task."""
        task = self._tasks.get(task_id)
        if task and task.state in (TaskState.PENDING, TaskState.RUNNING):
            task.state = TaskState.CANCELLED
            return True
        return False

    def get_task(self, task_id: str) -> Optional[AsyncTask]:
        return self._tasks.get(task_id)

    def get_results(self) -> Dict[str, Any]:
        """Get results of all completed tasks."""
        return {tid: t.result for tid, t in self._tasks.items()
                if t.state == TaskState.COMPLETED}

    def get_errors(self) -> Dict[str, str]:
        """Get errors of all failed tasks."""
        return {tid: t.error for tid, t in self._tasks.items()
                if t.state in (TaskState.FAILED, TaskState.TIMEOUT)}

    def list_tasks(self) -> List[Dict]:
        return [
            {"id": t.id, "name": t.name, "state": t.state.value,
             "progress": t.progress, "duration": round(t.duration, 3),
             "error": t.error}
            for t in self._tasks.values()
        ]

    def stats(self) -> Dict:
        states = [t.state for t in self._tasks.values()]
        return {
            "total": len(self._tasks),
            "pending": sum(1 for s in states if s == TaskState.PENDING),
            "running": sum(1 for s in states if s == TaskState.RUNNING),
            "completed": sum(1 for s in states if s == TaskState.COMPLETED),
            "failed": sum(1 for s in states if s == TaskState.FAILED),
            "timeout": sum(1 for s in states if s == TaskState.TIMEOUT),
            "cancelled": sum(1 for s in states if s == TaskState.CANCELLED),
            "max_concurrency": self.max_concurrency,
        }
