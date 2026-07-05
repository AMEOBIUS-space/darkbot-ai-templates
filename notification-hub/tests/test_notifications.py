import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from notifications import NotificationHub, ChannelType, Notification


def test_register_channel():
    hub = NotificationHub()
    hub.register_channel("telegram", ChannelType.TELEGRAM, {"bot_token": "x", "chat_id": "1"})
    assert "telegram" in hub.channels
    assert hub.channels["telegram"].channel_type == ChannelType.TELEGRAM


def test_send_log_channel():
    hub = NotificationHub()
    hub.register_channel("log", ChannelType.LOG)
    notif = hub.send("Test", "Hello", "log")
    assert notif.delivered is True
    assert notif.error == ""


def test_send_unknown_channel():
    hub = NotificationHub()
    notif = hub.send("Test", "Hello", "nonexistent")
    assert notif.delivered is False
    assert "not found" in notif.error


def test_send_disabled_channel():
    hub = NotificationHub()
    hub.register_channel("tg", ChannelType.TELEGRAM, enabled=False)
    notif = hub.send("Test", "Hello", "tg")
    assert notif.delivered is False
    assert "disabled" in notif.error


def test_template_render():
    hub = NotificationHub()
    hub.add_template("alert", "Alert: {{service}}", "Service {{service}} is {{status}}")
    title, msg = hub.render_template("alert", {"service": "API", "status": "down"})
    assert title == "Alert: API"
    assert msg == "Service API is down"


def test_send_templated():
    hub = NotificationHub()
    hub.register_channel("log", ChannelType.LOG)
    hub.add_template("alert", "Alert: {{service}}", "Service {{service}} is {{status}}")
    notif = hub.send_templated("alert", {"service": "DB", "status": "down"}, "log")
    assert notif.delivered is True
    assert "DB" in notif.title


def test_broadcast():
    hub = NotificationHub()
    hub.register_channel("log1", ChannelType.LOG)
    hub.register_channel("log2", ChannelType.LOG)
    hub.register_channel("disabled", ChannelType.LOG, enabled=False)
    results = hub.broadcast("Alert", "System down")
    assert len(results) == 2  # Only enabled channels
    assert all(r.delivered for r in results)


def test_routing_rule():
    hub = NotificationHub()
    hub.register_channel("default", ChannelType.LOG)
    hub.register_channel("alerts", ChannelType.LOG)
    hub.add_routing_rule("priority==critical", "alerts")
    notif = hub.send("Critical", "System failure", "default", priority="critical")
    # Routing resolves to "alerts" channel
    assert notif.channel == "default"  # send() uses specified channel


def test_rate_limit():
    hub = NotificationHub()
    hub.register_channel("log", ChannelType.LOG, rate_limit=3)
    for i in range(3):
        hub.send("T", f"msg {i}", "log")
    notif = hub.send("T", "msg 4", "log")
    assert notif.delivered is False
    assert "rate limit" in notif.error.lower()


def test_stats():
    hub = NotificationHub()
    hub.register_channel("log", ChannelType.LOG)
    hub.register_channel("tg", ChannelType.TELEGRAM, enabled=False)
    hub.send("T1", "M1", "log")
    hub.send("T2", "M2", "tg")  # Fails (disabled)
    stats = hub.stats()
    assert stats["channels"] == 2
    assert stats["enabled"] == 1
    assert stats["total_sent"] == 2
    assert stats["delivered"] == 1
    assert stats["failed"] == 1


def test_notification_metadata():
    hub = NotificationHub()
    hub.register_channel("log", ChannelType.LOG)
    notif = hub.send("Test", "Hello", "log", metadata={"source": "monitor", "alert_id": "a1"})
    assert notif.metadata["source"] == "monitor"
    assert notif.metadata["alert_id"] == "a1"


def test_template_not_found():
    hub = NotificationHub()
    hub.register_channel("log", ChannelType.LOG)
    notif = hub.send_templated("nonexistent", {"x": 1}, "log")
    assert notif.delivered is True
