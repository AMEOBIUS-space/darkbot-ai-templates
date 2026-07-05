import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from analyzer import LogParser, AnomalyDetector, LogStats, LogEntry


def test_parse_iso():
    entry = LogParser.parse_line("2026-07-05T12:00:00 ERROR Something went wrong")
    assert entry.parsed
    assert entry.level == "ERROR"
    assert "Something went wrong" in entry.message


def test_parse_bracket():
    entry = LogParser.parse_line("[2026-07-05 12:00:00] [INFO] Server started")
    assert entry.parsed
    assert entry.level == "INFO"


def test_parse_unparseable():
    entry = LogParser.parse_line("random text without format")
    assert not entry.parsed
    assert entry.level == "UNKNOWN"


def test_parse_multiple_formats():
    lines = [
        "2026-07-05T12:00:00 INFO Starting",
        "[2026-07-05 12:01:00] [ERROR] Failed",
        "garbage line",
    ]
    entries = LogParser.parse_lines(lines)
    assert len(entries) == 3
    assert entries[0].parsed
    assert entries[1].parsed
    assert not entries[2].parsed


def test_anomaly_error_spike():
    detector = AnomalyDetector(error_threshold=3)
    entries = [LogEntry("2026-01-01", "ERROR", f"Error {i}", parsed=True) for i in range(5)]
    anomalies = detector.detect(entries)
    assert any(a.type == "error_spike" for a in anomalies)


def test_anomaly_oom():
    detector = AnomalyDetector(error_threshold=100)
    entries = [LogEntry("2026-01-01", "CRITICAL", "out of memory: process killed")]
    anomalies = detector.detect(entries)
    assert any(a.type == "oom" for a in anomalies)
    assert any(a.severity == "CRITICAL" for a in anomalies)


def test_anomaly_auth_failure():
    detector = AnomalyDetector(error_threshold=100)
    entries = [LogEntry("2026-01-01", "WARNING", "auth failed for user admin")]
    anomalies = detector.detect(entries)
    assert any(a.type == "auth_failure" for a in anomalies)


def test_anomaly_no_anomalies():
    detector = AnomalyDetector(error_threshold=100)
    entries = [LogEntry("2026-01-01", "INFO", "All good")]
    anomalies = detector.detect(entries)
    assert len(anomalies) == 0


def test_stats_summary():
    entries = [
        LogEntry("t1", "INFO", "msg1"),
        LogEntry("t2", "ERROR", "msg2"),
        LogEntry("t3", "WARNING", "msg3"),
        LogEntry("t4", "ERROR", "msg4"),
    ]
    stats = LogStats.summary(entries)
    assert stats["total_entries"] == 4
    assert stats["errors"] == 2
    assert stats["warnings"] == 1


def test_stats_error_rate():
    entries = [
        LogEntry("t", "INFO", "ok"),
        LogEntry("t", "INFO", "ok"),
        LogEntry("t", "ERROR", "bad"),
        LogEntry("t", "ERROR", "bad"),
    ]
    rate = LogStats.error_rate(entries)
    assert rate == 50.0


def test_stats_empty():
    stats = LogStats.summary([])
    assert stats["total_entries"] == 0
    assert LogStats.error_rate([]) == 0.0


def test_top_messages():
    entries = [
        LogEntry("t", "INFO", "repeated message"),
        LogEntry("t", "INFO", "repeated message"),
        LogEntry("t", "INFO", "unique message"),
    ]
    top = LogStats.top_messages(entries, n=2)
    assert top[0][0] == "repeated message"
    assert top[0][1] == 2
