import sys, os, tempfile
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from migrations import MigrationManager


def test_add_migration():
    mgr = MigrationManager()
    mgr.add("001", "create_users", "CREATE TABLE users (id INTEGER PRIMARY KEY)", "DROP TABLE users")
    assert "001" in mgr.migrations


def test_migrate_up():
    mgr = MigrationManager()
    mgr.add("001", "create_users", "CREATE TABLE users (id INTEGER PRIMARY KEY)", "DROP TABLE users")
    count, applied = mgr.migrate_up()
    assert count == 1
    assert "001" in applied
    assert mgr.current_version() == "001"


def test_migrate_up_multiple():
    mgr = MigrationManager()
    mgr.add("001", "create_users", "CREATE TABLE users (id INTEGER PRIMARY KEY)", "DROP TABLE users")
    mgr.add("002", "add_email", "ALTER TABLE users ADD COLUMN email TEXT", "")
    mgr.add("003", "add_index", "CREATE INDEX idx_email ON users(email)", "DROP INDEX idx_email")
    count, applied = mgr.migrate_up()
    assert count == 3
    assert mgr.current_version() == "003"


def test_migrate_down():
    mgr = MigrationManager()
    mgr.add("001", "create_users", "CREATE TABLE users (id INTEGER PRIMARY KEY)", "DROP TABLE users")
    mgr.migrate_up()
    count, rolled_back = mgr.migrate_down()
    assert count == 1
    assert mgr.current_version() is None


def test_migrate_down_multiple():
    mgr = MigrationManager()
    mgr.add("001", "t1", "CREATE TABLE t1 (id INTEGER)", "DROP TABLE t1")
    mgr.add("002", "t2", "CREATE TABLE t2 (id INTEGER)", "DROP TABLE t2")
    mgr.migrate_up()
    count, _ = mgr.migrate_down(steps=2)
    assert count == 2
    assert mgr.current_version() is None


def test_pending():
    mgr = MigrationManager()
    mgr.add("001", "t1", "CREATE TABLE t1 (id INTEGER)", "DROP TABLE t1")
    mgr.add("002", "t2", "CREATE TABLE t2 (id INTEGER)", "DROP TABLE t2")
    assert len(mgr.pending()) == 2
    mgr.migrate_up()
    assert len(mgr.pending()) == 0


def test_current_version():
    mgr = MigrationManager()
    assert mgr.current_version() is None
    mgr.add("001", "t", "CREATE TABLE t (id INTEGER)", "DROP TABLE t")
    mgr.migrate_up()
    assert mgr.current_version() == "001"


def test_status():
    mgr = MigrationManager()
    mgr.add("001", "t1", "CREATE TABLE t1 (id INTEGER)", "DROP TABLE t1")
    mgr.add("002", "t2", "CREATE TABLE t2 (id INTEGER)", "DROP TABLE t2")
    mgr.migrate_up()
    status = mgr.status()
    assert status["applied"] == 2
    assert status["pending"] == 0
    assert status["current_version"] == "002"


def test_migrate_to_target():
    mgr = MigrationManager()
    mgr.add("001", "t1", "CREATE TABLE t1 (id INTEGER)", "DROP TABLE t1")
    mgr.add("002", "t2", "CREATE TABLE t2 (id INTEGER)", "DROP TABLE t2")
    mgr.add("003", "t3", "CREATE TABLE t3 (id INTEGER)", "DROP TABLE t3")
    mgr.migrate_up(target_version="002")
    assert mgr.current_version() == "002"
    assert len(mgr.pending()) == 1


def test_idempotent():
    mgr = MigrationManager()
    mgr.add("001", "t", "CREATE TABLE t (id INTEGER)", "DROP TABLE t")
    mgr.migrate_up()
    count, _ = mgr.migrate_up()  # Second call
    assert count == 0


def test_checksum_verification():
    mgr = MigrationManager()
    mgr.add("001", "t", "CREATE TABLE t (id INTEGER)", "DROP TABLE t")
    mgr.migrate_up()
    mismatches = mgr.verify_checksums()
    assert len(mismatches) == 0


def test_down_no_sql():
    mgr = MigrationManager()
    mgr.add("001", "t", "CREATE TABLE t (id INTEGER)", "")  # No down SQL
    mgr.migrate_up()
    count, _ = mgr.migrate_down()
    assert count == 0  # Can't rollback without down SQL


def test_persistence():
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name
    try:
        mgr1 = MigrationManager(db_path)
        mgr1.add("001", "t", "CREATE TABLE t (id INTEGER)", "DROP TABLE t")
        mgr1.migrate_up()
        mgr1.close()
        
        mgr2 = MigrationManager(db_path)
        assert mgr2.current_version() == "001"
        assert len(mgr2.pending()) == 0
        mgr2.close()
    finally:
        os.unlink(db_path)
