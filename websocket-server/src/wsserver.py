"""WebSocket Server — connection management, rooms, broadcast, heartbeat."""
import json
import time
import asyncio
import threading
from typing import Dict, List, Optional, Callable, Any, Set
from dataclasses import dataclass, asdict, field
from datetime import datetime
from enum import Enum
from collections import defaultdict


@dataclass
class Connection:
    id: str
    metadata: Dict = field(default_factory=dict)
    connected_at: str = ""
    rooms: Set[str] = field(default_factory=set)
    last_heartbeat: float = 0.0

    def __post_init__(self):
        if not self.connected_at:
            self.connected_at = datetime.now().isoformat()
        self.last_heartbeat = time.time()


class WebSocketRoomManager:
    """Manage WebSocket rooms/channels for group messaging."""

    def __init__(self):
        self._rooms: Dict[str, Set[str]] = defaultdict(set)  # room_name -> connection_ids
        self._connections: Dict[str, Connection] = {}
        self._handlers: Dict[str, List[Callable]] = defaultdict(list)
        self._middleware: List[Callable] = []

    def connect(self, conn_id: str, metadata: Dict = None) -> Connection:
        conn = Connection(id=conn_id, metadata=metadata or {})
        self._connections[conn_id] = conn
        return conn

    def disconnect(self, conn_id: str):
        conn = self._connections.pop(conn_id, None)
        if conn:
            for room in list(conn.rooms):
                self._rooms[room].discard(conn_id)
                if not self._rooms[room]:
                    del self._rooms[room]

    def join_room(self, conn_id: str, room: str) -> bool:
        if conn_id not in self._connections:
            return False
        self._connections[conn_id].rooms.add(room)
        self._rooms[room].add(conn_id)
        return True

    def leave_room(self, conn_id: str, room: str) -> bool:
        if conn_id not in self._connections:
            return False
        self._connections[conn_id].rooms.discard(room)
        self._rooms[room].discard(conn_id)
        if not self._rooms[room]:
            del self._rooms[room]
        return True

    def get_room_members(self, room: str) -> List[str]:
        return list(self._rooms.get(room, set()))

    def get_connection_rooms(self, conn_id: str) -> List[str]:
        conn = self._connections.get(conn_id)
        return list(conn.rooms) if conn else []

    def on(self, event: str, handler: Callable):
        self._handlers[event].append(handler)

    def use(self, middleware: Callable):
        self._middleware.append(middleware)

    def dispatch(self, event: str, data: Any, conn_id: str = None, room: str = None) -> List[str]:
        """Dispatch event to handlers. Returns list of target connection IDs."""
        targets = []

        if room:
            targets = list(self._rooms.get(room, set()))
        elif conn_id:
            targets = [conn_id]
        else:
            targets = list(self._connections.keys())

        # Run middleware
        for mw in self._middleware:
            try:
                mw(event, data, targets)
            except Exception:
                pass

        # Run handlers
        for handler in self._handlers.get(event, []):
            try:
                handler(event, data, targets)
            except Exception:
                pass

        return targets

    def broadcast(self, event: str, data: Any) -> List[str]:
        return self.dispatch(event, data)

    def broadcast_to_room(self, room: str, event: str, data: Any) -> List[str]:
        return self.dispatch(event, data, room=room)

    def send_to_connection(self, conn_id: str, event: str, data: Any) -> List[str]:
        return self.dispatch(event, data, conn_id=conn_id)

    def heartbeat(self, conn_id: str) -> bool:
        conn = self._connections.get(conn_id)
        if conn:
            conn.last_heartbeat = time.time()
            return True
        return False

    def cleanup_stale(self, max_age_seconds: float = 120) -> List[str]:
        """Remove connections that haven't sent heartbeat recently."""
        now = time.time()
        stale = [cid for cid, conn in self._connections.items()
                 if now - conn.last_heartbeat > max_age_seconds]
        for cid in stale:
            self.disconnect(cid)
        return stale

    def get_connection(self, conn_id: str) -> Optional[Connection]:
        return self._connections.get(conn_id)

    def list_connections(self) -> List[str]:
        return list(self._connections.keys())

    def list_rooms(self) -> List[str]:
        return list(self._rooms.keys())

    def room_count(self, room: str) -> int:
        return len(self._rooms.get(room, set()))

    def stats(self) -> Dict:
        return {
            "connections": len(self._connections),
            "rooms": len(self._rooms),
            "total_room_members": sum(len(m) for m in self._rooms.values()),
            "handlers": sum(len(h) for h in self._handlers.values()),
            "middleware": len(self._middleware),
        }
