import sys, os, time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from wsserver import WebSocketRoomManager, Connection


def test_connect():
    mgr = WebSocketRoomManager()
    conn = mgr.connect("conn1", {"user": "alice"})
    assert conn.id == "conn1"
    assert conn.metadata["user"] == "alice"
    assert "conn1" in mgr.list_connections()


def test_disconnect():
    mgr = WebSocketRoomManager()
    mgr.connect("conn1")
    mgr.disconnect("conn1")
    assert "conn1" not in mgr.list_connections()


def test_disconnect_removes_from_rooms():
    mgr = WebSocketRoomManager()
    mgr.connect("conn1")
    mgr.join_room("conn1", "general")
    mgr.disconnect("conn1")
    assert "conn1" not in mgr.get_room_members("general")


def test_join_room():
    mgr = WebSocketRoomManager()
    mgr.connect("conn1")
    assert mgr.join_room("conn1", "general") is True
    assert "conn1" in mgr.get_room_members("general")


def test_join_room_nonexistent_conn():
    mgr = WebSocketRoomManager()
    assert mgr.join_room("nonexistent", "room") is False


def test_leave_room():
    mgr = WebSocketRoomManager()
    mgr.connect("conn1")
    mgr.join_room("conn1", "general")
    mgr.leave_room("conn1", "general")
    assert "conn1" not in mgr.get_room_members("general")


def test_get_connection_rooms():
    mgr = WebSocketRoomManager()
    mgr.connect("conn1")
    mgr.join_room("conn1", "room1")
    mgr.join_room("conn1", "room2")
    rooms = mgr.get_connection_rooms("conn1")
    assert "room1" in rooms
    assert "room2" in rooms


def test_room_count():
    mgr = WebSocketRoomManager()
    mgr.connect("c1")
    mgr.connect("c2")
    mgr.join_room("c1", "general")
    mgr.join_room("c2", "general")
    assert mgr.room_count("general") == 2


def test_broadcast():
    mgr = WebSocketRoomManager()
    mgr.connect("c1")
    mgr.connect("c2")
    received = []
    mgr.on("message", lambda evt, data, targets: received.extend(targets))
    targets = mgr.broadcast("message", {"text": "hello"})
    assert len(targets) == 2
    assert len(received) == 2


def test_broadcast_to_room():
    mgr = WebSocketRoomManager()
    mgr.connect("c1")
    mgr.connect("c2")
    mgr.connect("c3")
    mgr.join_room("c1", "vip")
    mgr.join_room("c2", "vip")
    targets = mgr.broadcast_to_room("vip", "notification", {"msg": "VIP only"})
    assert len(targets) == 2
    assert "c3" not in targets


def test_send_to_connection():
    mgr = WebSocketRoomManager()
    mgr.connect("c1")
    mgr.connect("c2")
    targets = mgr.send_to_connection("c1", "private", {"data": "secret"})
    assert targets == ["c1"]


def test_heartbeat():
    mgr = WebSocketRoomManager()
    mgr.connect("c1")
    old_time = mgr.get_connection("c1").last_heartbeat
    time.sleep(0.01)
    mgr.heartbeat("c1")
    new_time = mgr.get_connection("c1").last_heartbeat
    assert new_time > old_time


def test_cleanup_stale():
    mgr = WebSocketRoomManager()
    conn = mgr.connect("c1")
    conn.last_heartbeat = time.time() - 200  # Very old
    mgr.connect("c2")  # Fresh
    stale = mgr.cleanup_stale(max_age_seconds=120)
    assert "c1" in stale
    assert "c2" not in stale
    assert "c1" not in mgr.list_connections()


def test_middleware():
    mgr = WebSocketRoomManager()
    mgr.connect("c1")
    log = []
    mgr.use(lambda evt, data, targets: log.append(f"{evt}:{len(targets)}"))
    mgr.broadcast("test", {})
    assert log == ["test:1"]


def test_handler_called():
    mgr = WebSocketRoomManager()
    mgr.connect("c1")
    results = []
    mgr.on("chat", lambda evt, data, targets: results.append(data))
    mgr.broadcast("chat", {"msg": "hi"})
    assert results == [{"msg": "hi"}]


def test_list_rooms():
    mgr = WebSocketRoomManager()
    mgr.connect("c1")
    mgr.join_room("c1", "room1")
    mgr.join_room("c1", "room2")
    rooms = mgr.list_rooms()
    assert "room1" in rooms
    assert "room2" in rooms


def test_stats():
    mgr = WebSocketRoomManager()
    mgr.connect("c1")
    mgr.connect("c2")
    mgr.join_room("c1", "room1")
    mgr.on("event", lambda e, d, t: None)
    stats = mgr.stats()
    assert stats["connections"] == 2
    assert stats["rooms"] == 1
    assert stats["handlers"] == 1


def test_get_connection():
    mgr = WebSocketRoomManager()
    mgr.connect("c1", {"role": "admin"})
    conn = mgr.get_connection("c1")
    assert conn is not None
    assert conn.metadata["role"] == "admin"
    assert mgr.get_connection("nonexistent") is None
