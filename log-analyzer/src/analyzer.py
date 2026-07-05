"""Log Analyzer & Anomaly Detector — parse logs, detect patterns, find anomalies."""
import re
import json
from typing import List, Dict, Tuple, Optional, Pattern
from dataclasses import dataclass, asdict, field
from collections import Counter, defaultdict
from datetime import datetime, timedelta


@dataclass
class LogEntry:
    timestamp: str
    level: str
    message: str
    source: str = ""
    raw: str = ""
    parsed: bool = True


@dataclass
class Anomaly:
    type: str
    severity: str
    description: str
    count: int
    first_seen: str
    last_seen: str
    pattern: str = ""
    sample: str = ""


class LogParser:
    """Parse log lines into structured entries."""

    PATTERNS = {
        "iso": re.compile(r'(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}[.\d]*Z?)\s+(\w+)\s+(.*)'),
        "syslog": re.compile(r'(\w{3}\s+\d+\s\d{2}:\d{2}:\d{2})\s+(\w+)\s+(.*)'),
        "bracket": re.compile(r'\[(\d{4}-\d{2}-\d{2}\s\d{2}:\d{2}:\d{2})\]\s+\[(\w+)\]\s+(.*)'),
        "simple": re.compile(r'(\d{4}-\d{2}-\d{2}\s\d{2}:\d{2}:\d{2})\s+(\w+)\s+(.*)'),
    }

    @classmethod
    def parse_line(cls, line: str) -> LogEntry:
        line = line.strip()
        for name, pattern in cls.PATTERNS.items():
            match = pattern.match(line)
            if match:
                return LogEntry(
                    timestamp=match.group(1),
                    level=match.group(2).upper(),
                    message=match.group(3),
                    raw=line,
                )
        return LogEntry(timestamp="", level="UNKNOWN", message=line, raw=line, parsed=False)

    @classmethod
    def parse_file(cls, filepath: str) -> List[LogEntry]:
        entries = []
        with open(filepath) as f:
            for line in f:
                if line.strip():
                    entries.append(cls.parse_line(line))
        return entries

    @classmethod
    def parse_lines(cls, lines: List[str]) -> List[LogEntry]:
        return [cls.parse_line(line) for line in lines if line.strip()]


class AnomalyDetector:
    """Detect anomalies in log entries."""

    def __init__(self, error_threshold: int = 10, time_window_minutes: int = 5):
        self.error_threshold = error_threshold
        self.time_window = timedelta(minutes=time_window_minutes)
        self.patterns: Dict[str, Pattern] = {
            "sql_error": re.compile(r'SQL|database|connection.*refused', re.I),
            "oom": re.compile(r'out.of.memory|OOM|killed.*process', re.I),
            "disk_full": re.compile(r'no.space.left|disk.full|ENOSPC', re.I),
            "auth_failure": re.compile(r'auth.*fail|invalid.*credential|access.*denied', re.I),
            "timeout": re.compile(r'timeout|timed.out|deadline.exceeded', re.I),
            "crash": re.compile(r'segfault|panic|core.dump|crash', re.I),
            "rate_limit": re.compile(r'rate.limit|too.many.requests|429|throttl', re.I),
        }

    def detect(self, entries: List[LogEntry]) -> List[Anomaly]:
        anomalies = []
        anomalies.extend(self._detect_error_spikes(entries))
        anomalies.extend(self._detect_patterns(entries))
        unparsed = [e for e in entries if not e.parsed]
        if unparsed:
            anomalies.append(Anomaly(
                type="unparsed_lines",
                severity="LOW",
                description=f"{len(unparsed)} lines could not be parsed",
                count=len(unparsed),
                first_seen=unparsed[0].raw[:80] if unparsed else "",
                last_seen=unparsed[-1].raw[:80] if unparsed else "",
            ))
        return anomalies

    def _detect_error_spikes(self, entries: List[LogEntry]) -> List[Anomaly]:
        anomalies = []
        error_entries = [e for e in entries if e.level in ("ERROR", "CRITICAL", "FATAL")]
        if len(error_entries) >= self.error_threshold:
            anomalies.append(Anomaly(
                type="error_spike",
                severity="HIGH" if len(error_entries) > 20 else "MEDIUM",
                description=f"{len(error_entries)} error-level entries detected",
                count=len(error_entries),
                first_seen=error_entries[0].timestamp,
                last_seen=error_entries[-1].timestamp,
                sample=error_entries[0].message[:100],
            ))
        return anomalies

    def _detect_patterns(self, entries: List[LogEntry]) -> List[Anomaly]:
        anomalies = []
        for name, pattern in self.patterns.items():
            matches = [e for e in entries if pattern.search(e.message)]
            if matches:
                severity = "CRITICAL" if name in ("oom", "crash", "disk_full") else "HIGH"
                anomalies.append(Anomaly(
                    type=name,
                    severity=severity,
                    description=f"Pattern '{name}' found in {len(matches)} entries",
                    count=len(matches),
                    first_seen=matches[0].timestamp,
                    last_seen=matches[-1].timestamp,
                    pattern=pattern.pattern,
                    sample=matches[0].message[:100],
                ))
        return anomalies


class LogStats:
    """Generate statistics from log entries."""

    @staticmethod
    def summary(entries: List[LogEntry]) -> Dict:
        levels = Counter(e.level for e in entries)
        return {
            "total_entries": len(entries),
            "parsed": sum(1 for e in entries if e.parsed),
            "unparsed": sum(1 for e in entries if not e.parsed),
            "by_level": dict(levels),
            "errors": levels.get("ERROR", 0) + levels.get("CRITICAL", 0) + levels.get("FATAL", 0),
            "warnings": levels.get("WARNING", 0) + levels.get("WARN", 0),
        }

    @staticmethod
    def top_messages(entries: List[LogEntry], n: int = 10) -> List[Tuple[str, int]]:
        messages = Counter(e.message[:100] for e in entries if e.parsed)
        return messages.most_common(n)

    @staticmethod
    def error_rate(entries: List[LogEntry]) -> float:
        if not entries:
            return 0.0
        errors = sum(1 for e in entries if e.level in ("ERROR", "CRITICAL", "FATAL"))
        return errors / len(entries) * 100
