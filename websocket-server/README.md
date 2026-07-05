# WebSocket Server

> Connection management, rooms, broadcast, heartbeat, and middleware

## Features

- Connection management (connect, disconnect, metadata)
- Room-based group messaging (join, leave, broadcast to room)
- Broadcast to all connections
- Send to specific connection
- Heartbeat tracking with stale cleanup
- Event handler registration
- Middleware support
- Statistics dashboard

## Quick Start

```python
from wsserver import WebSocketRoomManager

mgr = WebSocketRoomManager()
mgr.on("chat", lambda evt, data, targets: send_to_all(targets, data))

conn = mgr.connect("conn1", {"user": "alice"})
mgr.join_room("conn1", "general")

mgr.broadcast_to_room("general", "chat", {"msg": "Hello!"})
```

## Tests

```bash
python -m pytest tests/ -v
```

## License

MIT
