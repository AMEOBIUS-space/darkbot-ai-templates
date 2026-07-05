"""Event Bus — pub/sub with async support, priorities, and middleware."""
import asyncio
import threading
import time
from typing import Dict, List, Optional, Callable, Any, Set
from dataclasses import dataclass, asdict, field
from datetime import datetime
from enum import Enum
from collections import defaultdict


@dataclass
class Event:
    name: str
    data: Any = None
    timestamp: str = ""
    source: str = ""
    priority: int = 0  # Higher = processed first

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()


class EventBus:
    """Synchronous event bus with priority and middleware."""

    def __init__(self):
        self._handlers: Dict[str, List[tuple]] = defaultdict(list)  # name -> [(priority, handler)]
        self._middleware: List[Callable] = []
        self._events_log: List[Event] = []
        self._max_log = 500
        self._wildcard_handlers: List[Callable] = []

    def subscribe(self, event_name: str, handler: Callable, priority: int = 0):
        """Subscribe to an event. Higher priority handlers run first."""
        self._handlers[event_name].append((priority, handler))
        # Sort by priority (descending)
        self._handlers[event_name].sort(key=lambda x: -x[0])

    def subscribe_all(self, handler: Callable):
        """Subscribe to all events (wildcard)."""
        self._wildcard_handlers.append(handler)

    def unsubscribe(self, event_name: str, handler: Callable):
        """Remove a handler from an event."""
        if event_name in self._handlers:
            self._handlers[event_name] = [
                (p, h) for p, h in self._handlers[event_name] if h != handler
            ]

    def use(self, middleware: Callable):
        """Add middleware (called before handlers). Can modify or block event."""
        self._middleware.append(middleware)

    def publish(self, event_name: str, data: Any = None, source: str = "") -> int:
        """Publish an event synchronously. Returns number of handlers called."""
        event = Event(name=event_name, data=data, source=source)
        return self._dispatch(event)

    def _dispatch(self, event: Event) -> int:
        """Dispatch event to handlers."""
        # Log event
        self._events_log.append(event)
        if len(self._events_log) > self._max_log:
            self._events_log = self._events_log[-self._max_log:]

        # Run middleware
        for mw in self._middleware:
            try:
                result = mw(event)
                if result is False:
                    return 0  # Middleware blocked the event
            except Exception:
                pass

        called = 0

        # Wildcard handlers
        for handler in self._wildcard_handlers:
            try:
                handler(event)
                called += 1
            except Exception:
                pass

        # Named handlers (sorted by priority)
        for priority, handler in self._handlers.get(event.name, []):
            try:
                handler(event)
                called += 1
            except Exception:
                pass

        return called

    def get_history(self, event_name: str = None, limit: int = 100) -> List[Event]:
        """Get event history."""
        events = self._events_log
        if event_name:
            events = [e for e in events if e.name == event_name]
        return events[-limit:]

    def clear_history(self):
        self._events_log = []

    def handler_count(self, event_name: str = None) -> int:
        if event_name:
            return len(self._handlers.get(event_name, []))
        return sum(len(h) for h in self._handlers.values())

    def stats(self) -> Dict:
        return {
            "event_types": len(self._handlers),
            "total_handlers": self.handler_count(),
            "wildcard_handlers": len(self._wildcard_handlers),
            "middleware_count": len(self._middleware),
            "events_published": len(self._events_log),
        }


class AsyncEventBus:
    """Asynchronous event bus for async/await handlers."""

    def __init__(self):
        self._handlers: Dict[str, List[Callable]] = defaultdict(list)
        self._events_log: List[Event] = []
        self._max_log = 500

    def subscribe(self, event_name: str, handler: Callable):
        self._handlers[event_name].append(handler)

    async def publish(self, event_name: str, data: Any = None, source: str = "") -> int:
        event = Event(name=event_name, data=data, source=source)
        self._events_log.append(event)
        if len(self._events_log) > self._max_log:
            self._events_log = self._events_log[-self._max_log:]

        called = 0
        for handler in self._handlers.get(event_name, []):
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(event)
                else:
                    handler(event)
                called += 1
            except Exception:
                pass
        return called

    def stats(self) -> Dict:
        return {
            "event_types": len(self._handlers),
            "total_handlers": sum(len(h) for h in self._handlers.values()),
            "events_published": len(self._events_log),
        }
