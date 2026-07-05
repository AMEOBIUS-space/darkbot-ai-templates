import sys, os, asyncio
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from bus import EventBus, AsyncEventBus, Event


def test_subscribe_publish():
    bus = EventBus()
    received = []
    bus.subscribe("user.created", lambda e: received.append(e.data))
    bus.publish("user.created", {"name": "Alice"})
    assert received == [{"name": "Alice"}]


def test_multiple_handlers():
    bus = EventBus()
    results = []
    bus.subscribe("evt", lambda e: results.append("a"))
    bus.subscribe("evt", lambda e: results.append("b"))
    bus.publish("evt")
    assert "a" in results
    assert "b" in results
    assert len(results) == 2


def test_priority_order():
    bus = EventBus()
    order = []
    bus.subscribe("evt", lambda e: order.append("low"), priority=1)
    bus.subscribe("evt", lambda e: order.append("high"), priority=10)
    bus.subscribe("evt", lambda e: order.append("mid"), priority=5)
    bus.publish("evt")
    assert order == ["high", "mid", "low"]


def test_unsubscribe():
    bus = EventBus()
    received = []
    handler = lambda e: received.append(e.data)
    bus.subscribe("evt", handler)
    bus.unsubscribe("evt", handler)
    bus.publish("evt", "data")
    assert received == []


def test_wildcard():
    bus = EventBus()
    all_events = []
    bus.subscribe_all(lambda e: all_events.append(e.name))
    bus.publish("user.created")
    bus.publish("user.deleted")
    assert all_events == ["user.created", "user.deleted"]


def test_middleware():
    bus = EventBus()
    log = []
    bus.use(lambda e: log.append(f"mw:{e.name}"))
    bus.subscribe("evt", lambda e: log.append("handler"))
    bus.publish("evt")
    assert log == ["mw:evt", "handler"]


def test_middleware_block():
    bus = EventBus()
    called = []
    bus.use(lambda e: False)  # Block all events
    bus.subscribe("evt", lambda e: called.append(1))
    count = bus.publish("evt")
    assert count == 0
    assert called == []


def test_handler_error():
    bus = EventBus()
    bus.subscribe("evt", lambda e: 1/0)  # Will raise
    bus.subscribe("evt", lambda e: None)  # Should still run
    count = bus.publish("evt")
    assert count == 1  # Only the second handler succeeded


def test_history():
    bus = EventBus()
    bus.publish("evt1", "a")
    bus.publish("evt2", "b")
    history = bus.get_history()
    assert len(history) == 2
    assert history[0].name == "evt1"


def test_history_filtered():
    bus = EventBus()
    bus.publish("a", 1)
    bus.publish("b", 2)
    bus.publish("a", 3)
    history = bus.get_history(event_name="a")
    assert len(history) == 2
    assert all(e.name == "a" for e in history)


def test_clear_history():
    bus = EventBus()
    bus.publish("evt")
    bus.clear_history()
    assert len(bus.get_history()) == 0


def test_handler_count():
    bus = EventBus()
    bus.subscribe("a", lambda e: None)
    bus.subscribe("a", lambda e: None)
    bus.subscribe("b", lambda e: None)
    assert bus.handler_count("a") == 2
    assert bus.handler_count("b") == 1
    assert bus.handler_count() == 3


def test_stats():
    bus = EventBus()
    bus.subscribe("evt", lambda e: None)
    bus.subscribe_all(lambda e: None)
    bus.use(lambda e: None)
    bus.publish("evt")
    stats = bus.stats()
    assert stats["event_types"] == 1
    assert stats["total_handlers"] == 1
    assert stats["wildcard_handlers"] == 1
    assert stats["middleware_count"] == 1
    assert stats["events_published"] == 1


def test_event_data():
    event = Event(name="test", data={"key": "value"})
    assert event.name == "test"
    assert event.data == {"key": "value"}
    assert event.timestamp  # Auto-generated


def test_async_publish():
    async def run():
        bus = AsyncEventBus()
        received = []
        async def handler(event):
            received.append(event.data)
        bus.subscribe("async.evt", handler)
        count = await bus.publish("async.evt", {"x": 1})
        assert count == 1
        assert received == [{"x": 1}]
    asyncio.run(run())


def test_async_sync_handler():
    async def run():
        bus = AsyncEventBus()
        received = []
        bus.subscribe("evt", lambda e: received.append(e.data))
        await bus.publish("evt", "sync_handler")
        assert received == ["sync_handler"]
    asyncio.run(run())


def test_async_stats():
    async def run():
        bus = AsyncEventBus()
        bus.subscribe("a", lambda e: None)
        await bus.publish("a")
        stats = bus.stats()
        assert stats["events_published"] == 1
    asyncio.run(run())
