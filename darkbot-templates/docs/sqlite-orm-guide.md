# SQLite ORM: Query Builder Without SQLAlchemy

> Part of the [darkbot-templates](https://github.com/AMEOBIUS-space/darkbot-ai-templates) series — zero-dependency production templates.

SQLAlchemy is powerful, but it's heavy. For CLI tools, bots, and small services that just need SQLite with a clean API, this template gives you a fluent query builder with zero dependencies.

## Usage

```python
from darkbot_templates.templates.sqlite_orm import Database

db = Database("app.db")  # or ":memory:" for testing

# Create table
db.create_table("users", {
    "id": "INTEGER PRIMARY KEY AUTOINCREMENT",
    "name": "TEXT NOT NULL",
    "email": "TEXT UNIQUE",
    "role": "TEXT DEFAULT 'user'",
    "created_at": "REAL",
})

# Insert
db.table("users").insert({"name": "Alice", "email": "alice@example.com", "created_at": time.time()})

# Query
users = db.table("users").where("role", "=", "admin").all()
# → [{"id": 1, "name": "Alice", "email": "alice@example.com", ...}]

user = db.table("users").where("email", "=", "alice@example.com").first()
```

## Fluent Query Builder

```python
# SELECT with WHERE, ORDER BY, LIMIT
results = (
    db.table("orders")
    .select("id", "amount", "status")
    .where("status", "=", "completed")
    .where("amount", ">", 100)
    .order_by("amount", descending=True)
    .limit(10)
    .all()
)

# COUNT
count = db.table("users").where("role", "=", "admin").count()

# UPDATE
db.table("users").where("id", "=", 42).update({"role": "admin"})

# DELETE
db.table("users").where("id", "=", 99).delete()
```

## Multiple WHERE Conditions

```python
# AND (chained where)
db.table("orders").where("status", "=", "paid").where("amount", ">", 50).all()

# Operators: =, !=, >, <, >=, <=, LIKE, IN, IS NULL
db.table("users").where("name", "LIKE", "%alice%").all()
db.table("orders").where("status", "IN", ("pending", "processing")).all()
db.table("users").where("deleted_at", "IS NULL").all()
```

## Raw SQL When Needed

```python
# Full control when the builder isn't enough
db.execute("CREATE INDEX IF NOT EXISTS idx_email ON users(email)")

rows = db.query("SELECT u.name, COUNT(o.id) as order_count FROM users u JOIN orders o ON u.id = o.user_id GROUP BY u.id")
# → [{"name": "Alice", "order_count": 15}, ...]

one = db.query_one("SELECT * FROM users WHERE id = ?", (42,))
```

## WAL Mode + Foreign Keys

By default, the Database enables:
- `PRAGMA journal_mode=WAL` — better concurrency for multi-threaded access
- `PRAGMA foreign_keys=ON` — referential integrity

## Migration Pattern

```python
def migrate(db):
    # Check if column exists
    cols = db.query("PRAGMA table_info(users)")
    col_names = [c["name"] for c in cols]

    if "phone" not in col_names:
        db.execute("ALTER TABLE users ADD COLUMN phone TEXT")

    if "verified" not in col_names:
        db.execute("ALTER TABLE users ADD COLUMN verified INTEGER DEFAULT 0")

db = Database("app.db")
migrate(db)
```

## Freelance Bot Storage

```python
db = Database("freelance.db")

db.create_table("bids", {
    "id": "INTEGER PRIMARY KEY AUTOINCREMENT",
    "platform": "TEXT NOT NULL",
    "job_id": "TEXT NOT NULL",
    "amount": "REAL",
    "status": "TEXT DEFAULT 'sent'",
    "created_at": "REAL",
})

# Track a bid
db.table("bids").insert({
    "platform": "kwork",
    "job_id": "3212993",
    "amount": 45000,
    "created_at": time.time(),
})

# Check pending
pending = db.table("bids").where("status", "=", "sent").all()
print(f"{len(pending)} bids awaiting response")

# Update status
db.table("bids").where("job_id", "=", "3212993").update({"status": "accepted"})
```

## Connection Pool Integration

```python
from darkbot_templates.templates.connection_pool import ConnectionPool
from darkbot_templates.templates.sqlite_orm import Database

# For multi-threaded access, wrap with connection pool
pool = ConnectionPool(
    factory=lambda: Database("app.db").conn,
    destroyer=lambda c: c.close(),
    min_size=2,
    max_size=5,
)

with pool.acquire() as conn:
    cursor = conn.execute("SELECT * FROM users")
    rows = cursor.fetchall()
```

## Testing

```bash
pytest tests/test_sqlite_orm.py -v
```

## References

- [sqlite3 docs](https://docs.python.org/3/library/sqlite3.html)
- [SQLite WAL Mode](https://www.sqlite.org/wal.html)

---

*darkbot-templates v1.8.5 — 30 templates, zero dependencies, 448 tests.*
