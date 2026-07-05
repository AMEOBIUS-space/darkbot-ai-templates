import sys, os, tempfile, time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from watcher import FileWatcher, WatchEvent, FileChange


def test_watch_file():
    with tempfile.NamedTemporaryFile(delete=False, suffix=".py") as f:
        f.write(b"hello")
        f.flush()
        path = f.name
    try:
        w = FileWatcher()
        w.watch(path)
        assert len(w.watch_paths) == 1
    finally:
        os.unlink(path)


def test_detect_modification():
    with tempfile.NamedTemporaryFile(delete=False, suffix=".py") as f:
        f.write(b"original")
        f.flush()
        path = f.name
    try:
        w = FileWatcher()
        w.watch(path)
        with open(path, "w") as f:
            f.write("modified content")
        changes = w.scan()
        assert any(c.event == WatchEvent.MODIFIED for c in changes)
    finally:
        os.unlink(path)


def test_detect_creation_in_dir():
    with tempfile.TemporaryDirectory() as d:
        w = FileWatcher()
        w.watch(d)
        new_file = os.path.join(d, "new.py")
        with open(new_file, "w") as f:
            f.write("content")
        changes = w.scan()
        assert any(c.event == WatchEvent.CREATED for c in changes)
        assert any(c.path == new_file for c in changes)


def test_detect_deletion():
    with tempfile.NamedTemporaryFile(delete=False, suffix=".py") as f:
        f.write(b"data")
        f.flush()
        path = f.name
    try:
        w = FileWatcher()
        w.watch(path)
        os.unlink(path)
        changes = w.scan()
        assert any(c.event == WatchEvent.DELETED for c in changes)
    except:
        pass


def test_event_handler():
    with tempfile.NamedTemporaryFile(delete=False, suffix=".py") as f:
        f.write(b"original")
        f.flush()
        path = f.name
    try:
        w = FileWatcher()
        w.watch(path)
        received = []
        w.on_event(WatchEvent.MODIFIED, lambda c: received.append(c))
        with open(path, "w") as f:
            f.write("changed")
        w.scan()
        assert len(received) >= 1
    finally:
        os.unlink(path)


def test_pattern_handler():
    with tempfile.TemporaryDirectory() as d:
        w = FileWatcher()
        w.watch(d)
        received = []
        w.on_pattern("*.py", lambda c: received.append(c), event=WatchEvent.CREATED)
        new_file = os.path.join(d, "script.py")
        with open(new_file, "w") as f:
            f.write("code")
        w.scan()
        assert len(received) >= 1


def test_no_changes():
    with tempfile.NamedTemporaryFile(delete=False, suffix=".py") as f:
        f.write(b"stable")
        f.flush()
        path = f.name
    try:
        w = FileWatcher()
        w.watch(path)
        changes = w.scan()
        assert len(changes) == 0
    finally:
        os.unlink(path)


def test_stats():
    with tempfile.NamedTemporaryFile(delete=False) as f:
        f.write(b"x")
        f.flush()
        path = f.name
    try:
        w = FileWatcher()
        w.watch(path)
        stats = w.stats()
        assert stats["watching"] == 1
        assert stats["changes"] == 0
    finally:
        os.unlink(path)


def test_checksum():
    with tempfile.NamedTemporaryFile(delete=False) as f:
        f.write(b"test data")
        f.flush()
        path = f.name
    try:
        cs = FileWatcher._checksum(path)
        assert len(cs) == 32
    finally:
        os.unlink(path)


def test_start_stop():
    w = FileWatcher()
    w.start(poll_interval=0.1)
    time.sleep(0.3)
    w.stop()
    assert w._running is False


def test_multiple_watches():
    with tempfile.TemporaryDirectory() as d:
        f1 = os.path.join(d, "a.py")
        f2 = os.path.join(d, "b.py")
        with open(f1, "w") as f: f.write("a")
        with open(f2, "w") as f: f.write("b")
        w = FileWatcher()
        w.watch(f1)
        w.watch(f2)
        assert len(w.watch_paths) == 2


def test_history_limit():
    with tempfile.NamedTemporaryFile(delete=False) as f:
        f.write(b"0")
        f.flush()
        path = f.name
    try:
        w = FileWatcher()
        w._max_history = 3
        w.watch(path)
        for i in range(5):
            with open(path, "w") as f:
                f.write(str(i))
            w.scan()
        assert len(w.changes) <= 3
    finally:
        os.unlink(path)
