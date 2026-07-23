# Log Analyzer: Parse and Aggregate Logs Without ELK

> Part of the [darkbot-templates](https://github.com/AMEOBIUS-space/darkbot-ai-templates) series — zero-dependency production templates.

SSH'd into a server, staring at a 2GB log file, and `grep` isn't enough. You need level filtering, time-range queries, and aggregation. This template parses both structured (JSON) and unstructured logs in pure Python.

## Usage

```python
from darkbot_templates.templates.log_analyzer import LogAnalyzer

analyzer = LogAnalyzer()

# Load from file
analyzer.load_file("/var/log/app.log")

# Or from string
analyzer.load_text("""
2025-01-15 10:00:01 INFO  Server started on port 8080
2025-01-15 10:00:05 INFO  Database connected
2025-01-15 10:01:00 WARN  Slow query: 2.3s
2025-01-15 10:01:30 ERROR Connection timeout
2025-01-15 10:02:00 ERROR Connection timeout
2025-01-15 10:03:00 INFO  Retry succeeded
""")

# Filter by level
errors = analyzer.filter(level="ERROR")
# → 2 entries

# Filter by pattern
timeouts = analyzer.filter(pattern="timeout")
# → 2 entries

# Time range
range_logs = analyzer.filter(time_range=("2025-01-15 10:01:00", "2025-01-15 10:02:00"))
```

## Level Distribution

```python
stats = analyzer.level_counts()
# {"INFO": 3, "WARN": 1, "ERROR": 2}
```

## Top Messages

```python
top = analyzer.top_messages(n=5)
# [("Connection timeout", 2), ("Server started on port 8080", 1), ...]
```

Find repeating errors instantly — the top message is usually the smoking gun.

## Structured JSON Logs

```python
analyzer = LogAnalyzer()
analyzer.load_file("app.jsonl")  # one JSON object per line

# Filter by structured field
payment_errors = analyzer.filter(
    level="ERROR",
    fields={"service": "payment", "error_type": "timeout"}
)
```

## Time-Range Queries

```python
from datetime import datetime

# What happened in the last hour?
recent = analyzer.filter(
    time_range=(datetime.now() - timedelta(hours=1), datetime.now())
)

# Error spike investigation
spike = analyzer.filter(
    level="ERROR",
    time_range=("2025-01-15 10:01:00", "2025-01-15 10:05:00")
)
```

## Export Aggregated Report

```python
report = analyzer.summary()
# {
#   "total_entries": 10000,
#   "level_counts": {"INFO": 8500, "WARN": 1200, "ERROR": 300},
#   "time_range": ("2025-01-15 10:00:01", "2025-01-15 22:00:00"),
#   "top_messages": [("Connection timeout", 150), ...],
#   "top_sources": [("payment", 200), ("auth", 80), ...]
# }
```

## Freelance Platform Log Monitoring

```python
analyzer = LogAnalyzer()
analyzer.load_file("~/.hermes/logs/gateway.log")

# Check for platform errors
kwork_errors = analyzer.filter(pattern="kwork", level="ERROR")
laborx_warns = analyzer.filter(pattern="laborx", level="WARN")

print(f"Kwork errors: {len(kwork_errors)}")
print(f"LaborX warnings: {len(laborx_warns)}")
```

## Supported Log Formats

The parser auto-detects:
- `YYYY-MM-DD HH:MM:SS LEVEL message` (standard)
- `YYYY-MM-DDTHH:MM:SS LEVEL message` (ISO)
- `YYYY-MM-DD HH:MM:SS,mmm LEVEL message` (Java)
- `{"timestamp": "...", "level": "...", "message": "..."}` (JSON)
- `Mon DD HH:MM:SS ...` (syslog)

## Testing

```bash
pytest tests/test_log_csv.py -v
```

## References

- [Structured Logging (JSON)](https://www.sumologic.com/blog/json-logs/)
- [Log Aggregation Patterns](https://martinfowler.com/articles/patterns-of-distributed-systems/log-aggregation.html)

---

*darkbot-templates v1.8.5 — 30 templates, zero dependencies, 448 tests.*
