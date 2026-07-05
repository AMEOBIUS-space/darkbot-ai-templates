"""Metrics Collector — counters, gauges, histograms, and timers for app monitoring."""
import time
import json
import threading
from typing import Dict, List, Optional, Callable
from dataclasses import dataclass, asdict, field
from collections import defaultdict
from datetime import datetime


@dataclass
class Counter:
    name: str
    value: float = 0.0
    labels: Dict = field(default_factory=dict)
    help: str = ""

    def inc(self, amount: float = 1.0):
        self.value += amount

    def reset(self):
        self.value = 0.0


@dataclass
class Gauge:
    name: str
    value: float = 0.0
    labels: Dict = field(default_factory=dict)
    help: str = ""

    def set(self, value: float):
        self.value = value

    def inc(self, amount: float = 1.0):
        self.value += amount

    def dec(self, amount: float = 1.0):
        self.value -= amount


@dataclass
class Histogram:
    name: str
    buckets: List[float] = field(default_factory=lambda: [0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0])
    counts: List[int] = field(default_factory=list)
    sum_value: float = 0.0
    total_count: int = 0
    labels: Dict = field(default_factory=dict)
    help: str = ""

    def __post_init__(self):
        if not self.counts:
            self.counts = [0] * len(self.buckets)

    def observe(self, value: float):
        self.sum_value += value
        self.total_count += 1
        for i, bound in enumerate(self.buckets):
            if value <= bound:
                self.counts[i] += 1
                break
        else:
            if self.counts:
                self.counts[-1] += 1

    def percentile(self, p: float) -> Optional[float]:
        if self.total_count == 0:
            return None
        if not self.buckets:
            return None
        target = self.total_count * p
        cumulative = 0
        for i, count in enumerate(self.counts):
            cumulative += count
            if cumulative >= target:
                return self.buckets[i] if i < len(self.buckets) else self.buckets[-1]
        return self.buckets[-1]

    def avg(self) -> float:
        return self.sum_value / self.total_count if self.total_count > 0 else 0.0


class Timer:
    """Context manager and decorator for timing operations."""

    def __init__(self, histogram: Histogram):
        self.histogram = histogram
        self._start = 0.0

    def __enter__(self):
        self._start = time.time()
        return self

    def __exit__(self, *args):
        elapsed = time.time() - self._start
        self.histogram.observe(elapsed)

    def __call__(self, func: Callable):
        def wrapper(*args, **kwargs):
            with self:
                return func(*args, **kwargs)
        return wrapper


class MetricsCollector:
    """Collect and export application metrics."""

    def __init__(self):
        self.counters: Dict[str, Counter] = {}
        self.gauges: Dict[str, Gauge] = {}
        self.histograms: Dict[str, Histogram] = {}
        self._lock = threading.Lock()

    def counter(self, name: str, help: str = "") -> Counter:
        with self._lock:
            if name not in self.counters:
                self.counters[name] = Counter(name=name, help=help)
            return self.counters[name]

    def gauge(self, name: str, help: str = "") -> Gauge:
        with self._lock:
            if name not in self.gauges:
                self.gauges[name] = Gauge(name=name, help=help)
            return self.gauges[name]

    def histogram(self, name: str, buckets: List[float] = None, help: str = "") -> Histogram:
        with self._lock:
            if name not in self.histograms:
                self.histograms[name] = Histogram(name=name, buckets=buckets or [], help=help)
            return self.histograms[name]

    def timer(self, name: str, help: str = "") -> Timer:
        hist = self.histogram(name, help=help)
        return Timer(hist)

    def export_json(self) -> Dict:
        """Export all metrics as JSON."""
        with self._lock:
            return {
                "counters": {k: {"value": v.value, "help": v.help} for k, v in self.counters.items()},
                "gauges": {k: {"value": v.value, "help": v.help} for k, v in self.gauges.items()},
                "histograms": {
                    k: {"sum": v.sum_value, "count": v.total_count, "avg": v.avg(),
                        "p50": v.percentile(0.5), "p95": v.percentile(0.95), "p99": v.percentile(0.99),
                        "buckets": dict(zip(v.buckets, v.counts)), "help": v.help}
                    for k, v in self.histograms.items()
                },
            }

    def export_prometheus(self) -> str:
        """Export metrics in Prometheus text format."""
        lines = []
        for name, c in self.counters.items():
            if c.help:
                lines.append(f"# HELP {name} {c.help}")
            lines.append(f"# TYPE {name} counter")
            lines.append(f"{name} {c.value}")

        for name, g in self.gauges.items():
            if g.help:
                lines.append(f"# HELP {name} {g.help}")
            lines.append(f"# TYPE {name} gauge")
            lines.append(f"{name} {g.value}")

        for name, h in self.histograms.items():
            if h.help:
                lines.append(f"# HELP {name} {h.help}")
            lines.append(f"# TYPE {name} histogram")
            cumulative = 0
            for i, bound in enumerate(h.buckets):
                cumulative = h.counts[i]
                lines.append(f'{name}_bucket{{le="{bound}"}} {cumulative}')
            lines.append(f'{name}_bucket{{le="+Inf"}} {h.total_count}')
            lines.append(f"{name}_sum {h.sum_value}")
            lines.append(f"{name}_count {h.total_count}")

        return "\n".join(lines)

    def reset(self):
        """Reset all metrics."""
        with self._lock:
            for c in self.counters.values():
                c.reset()
            for g in self.gauges.values():
                g.set(0.0)
            for h in self.histograms.values():
                h.counts = [0] * len(h.buckets)
                h.sum_value = 0.0
                h.total_count = 0
