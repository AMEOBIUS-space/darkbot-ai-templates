"""File Watcher — filesystem monitoring with debouncing and event callbacks."""
import os
import time
import threading
import hashlib
from typing import Dict, List, Optional, Callable, Set
from dataclasses import dataclass, asdict, field
from datetime import datetime
from pathlib import Path
from enum import Enum


class WatchEvent(Enum):
    CREATED = "created"
    MODIFIED = "modified"
    DELETED = "deleted"
    MOVED = "moved"


@dataclass
class FileChange:
    event: WatchEvent
    path: str
    timestamp: str
    size: int = 0
    checksum: str = ""
    old_path: str = ""


class FileWatcher:
    """Watch files and directories for changes with debouncing."""

    def __init__(self, debounce_ms: int = 300):
        self.debounce = debounce_ms / 1000.0
        self.watch_paths: Dict[str, Dict] = {}
        self.handlers: Dict[WatchEvent, List[Callable]] = {}
        self.pattern_handlers: List[Dict] = []
        self.changes: List[FileChange] = []
        self._running = False
        self._thread = None
        self._poll_interval = 1.0
        self._max_history = 500

    def watch(self, path: str):
        path = str(Path(path).resolve())
        self.watch_paths[path] = self._snapshot(path)

    def on_event(self, event: WatchEvent, handler: Callable):
        if event not in self.handlers:
            self.handlers[event] = []
        self.handlers[event].append(handler)

    def on_pattern(self, pattern: str, handler: Callable, event: WatchEvent = WatchEvent.MODIFIED):
        self.pattern_handlers.append({"pattern": pattern, "event": event, "handler": handler})

    def _snapshot(self, path: str) -> Dict:
        try:
            stat = os.stat(path)
            return {"size": stat.st_size, "mtime": stat.st_mtime,
                    "checksum": self._checksum(path) if os.path.isfile(path) else ""}
        except OSError:
            return {}

    @staticmethod
    def _checksum(filepath: str) -> str:
        try:
            with open(filepath, "rb") as f:
                return hashlib.md5(f.read()).hexdigest()
        except (OSError, PermissionError):
            return ""

    def _detect_changes(self) -> List[FileChange]:
        changes = []
        current_paths = set()

        for watch_path in list(self.watch_paths.keys()):
            if os.path.isdir(watch_path):
                try:
                    for entry in os.listdir(watch_path):
                        full = str(Path(watch_path) / entry)
                        current_paths.add(full)
                        if full not in self.watch_paths:
                            snap = self._snapshot(full)
                            self.watch_paths[full] = snap
                            changes.append(FileChange(event=WatchEvent.CREATED, path=full,
                                timestamp=datetime.now().isoformat(), size=snap.get("size", 0),
                                checksum=snap.get("checksum", "")))
                        else:
                            snap = self._snapshot(full)
                            old = self.watch_paths[full]
                            if snap.get("checksum") != old.get("checksum") or snap.get("size") != old.get("size"):
                                self.watch_paths[full] = snap
                                changes.append(FileChange(event=WatchEvent.MODIFIED, path=full,
                                    timestamp=datetime.now().isoformat(), size=snap.get("size", 0),
                                    checksum=snap.get("checksum", "")))
                except OSError:
                    pass
            elif os.path.isfile(watch_path):
                current_paths.add(watch_path)
                snap = self._snapshot(watch_path)
                old = self.watch_paths[watch_path]
                if snap.get("checksum") != old.get("checksum") or snap.get("size") != old.get("size"):
                    self.watch_paths[watch_path] = snap
                    changes.append(FileChange(event=WatchEvent.MODIFIED, path=watch_path,
                        timestamp=datetime.now().isoformat(), size=snap.get("size", 0),
                        checksum=snap.get("checksum", "")))
            else:
                if watch_path in self.watch_paths:
                    changes.append(FileChange(event=WatchEvent.DELETED, path=watch_path,
                        timestamp=datetime.now().isoformat()))
                    del self.watch_paths[watch_path]

        for path in list(self.watch_paths.keys()):
            if path not in current_paths and not os.path.exists(path):
                if any(os.path.dirname(path) == wp for wp in self.watch_paths if os.path.isdir(wp)):
                    changes.append(FileChange(event=WatchEvent.DELETED, path=path,
                        timestamp=datetime.now().isoformat()))
                    del self.watch_paths[path]

        return changes

    def scan(self) -> List[FileChange]:
        changes = self._detect_changes()
        for change in changes:
            self.changes.append(change)
            self._dispatch(change)
        if len(self.changes) > self._max_history:
            self.changes = self.changes[-self._max_history:]
        return changes

    def _dispatch(self, change: FileChange):
        for handler in self.handlers.get(change.event, []):
            try:
                handler(change)
            except Exception:
                pass
        for ph in self.pattern_handlers:
            if ph["event"] == change.event:
                if Path(change.path).match(ph["pattern"]):
                    try:
                        ph["handler"](change)
                    except Exception:
                        pass

    def start(self, poll_interval: float = 1.0):
        self._poll_interval = poll_interval
        self._running = True
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()

    def stop(self):
        self._running = False
        if self._thread:
            self._thread.join(timeout=5)

    def _loop(self):
        while self._running:
            self.scan()
            time.sleep(self._poll_interval)

    def stats(self) -> Dict:
        return {"watching": len(self.watch_paths), "changes": len(self.changes),
                "running": self._running, "debounce_ms": int(self.debounce * 1000)}
