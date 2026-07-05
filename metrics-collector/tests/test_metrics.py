import sys, os, time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from metrics import MetricsCollector, Counter, Gauge, Histogram, Timer


def test_counter():
    c = Counter(name="requests")
    c.inc()
    c.inc(5)
    assert c.value == 6
    c.reset()
    assert c.value == 0


def test_gauge():
    g = Gauge(name="temperature")
    g.set(25.5)
    assert g.value == 25.5
    g.inc(2.5)
    assert g.value == 28.0
    g.dec(3.0)
    assert g.value == 25.0


def test_histogram_observe():
    h = Histogram(name="latency")
    h.observe(0.05)
    h.observe(0.15)
    h.observe(0.5)
    assert h.total_count == 3
    assert h.sum_value == 0.7


def test_histogram_percentile():
    h = Histogram(name="latency", buckets=[0.1, 0.5, 1.0, 5.0])
    for v in [0.05, 0.2, 0.3, 0.6, 0.8]:
        h.observe(v)
    p50 = h.percentile(0.5)
    assert p50 is not None
    assert p50 <= 1.0


def test_histogram_avg():
    h = Histogram(name="duration")
    h.observe(1.0)
    h.observe(3.0)
    assert h.avg() == 2.0


def test_histogram_empty():
    h = Histogram(name="empty")
    assert h.avg() == 0.0
    assert h.percentile(0.5) is None


def test_timer_context_manager():
    h = Histogram(name="timer_test")
    timer = Timer(h)
    with timer:
        time.sleep(0.01)
    assert h.total_count == 1
    assert h.sum_value > 0


def test_timer_decorator():
    h = Histogram(name="decorator_test")
    timer = Timer(h)

    @timer
    def slow_function():
        time.sleep(0.01)
        return "done"

    result = slow_function()
    assert result == "done"
    assert h.total_count == 1


def test_collector_counter():
    m = MetricsCollector()
    c = m.counter("http_requests", "Total HTTP requests")
    c.inc(10)
    assert m.counters["http_requests"].value == 10


def test_collector_gauge():
    m = MetricsCollector()
    g = m.gauge("active_connections", "Active connections")
    g.set(42)
    assert m.gauges["active_connections"].value == 42


def test_collector_histogram():
    m = MetricsCollector()
    h = m.histogram("response_time", help="Response time in seconds")
    h.observe(0.1)
    h.observe(0.5)
    assert m.histograms["response_time"].total_count == 2


def test_collector_timer():
    m = MetricsCollector()
    timer = m.timer("db_query", "Database query time")
    with timer:
        time.sleep(0.01)
    assert m.histograms["db_query"].total_count == 1


def test_export_json():
    m = MetricsCollector()
    m.counter("reqs").inc(5)
    m.gauge("temp").set(20)
    h = m.histogram("latency")
    h.observe(0.1)
    data = m.export_json()
    assert "counters" in data
    assert data["counters"]["reqs"]["value"] == 5
    assert data["gauges"]["temp"]["value"] == 20
    assert data["histograms"]["latency"]["count"] == 1


def test_export_prometheus():
    m = MetricsCollector()
    m.counter("requests", "Total requests").inc(10)
    m.gauge("memory", "Memory usage").set(512)
    output = m.export_prometheus()
    assert "requests" in output
    assert "10" in output
    assert "memory" in output
    assert "# TYPE requests counter" in output


def test_reset():
    m = MetricsCollector()
    m.counter("c1").inc(10)
    m.gauge("g1").set(50)
    m.reset()
    assert m.counters["c1"].value == 0
    assert m.gauges["g1"].value == 0.0


def test_counter_idempotent():
    m = MetricsCollector()
    c1 = m.counter("requests")
    c2 = m.counter("requests")
    assert c1 is c2
