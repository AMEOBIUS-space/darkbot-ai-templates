# Database Migration Tool

> Versioned schema migrations with rollback support for SQLite

## Features

- Versioned migrations (001, 002, 003...)
- Up and down (rollback) SQL for each migration
- Migration tracking table (_migrations)
- Checksum verification (detect tampered migrations)
- Target version migration
- Pending detection
- Persistence across sessions
- Idempotent (safe to call multiple times)
- Status dashboard

## Quick Start

```python
from migrations import MigrationManager

mgr = MigrationManager("app.db")
mgr.add("001", "create_users", "CREATE TABLE users (id INTEGER)", "DROP TABLE users")
mgr.add("002", "add_email", "ALTER TABLE users ADD COLUMN email TEXT", "")
mgr.migrate_up()
print(mgr.status())
```

## Tests

```bash
python -m pytest tests/ -v
```

## License

MIT

Freelance portfolio: [https://ameobius-space.github.io/kwork-portfolio/](https://ameobius-space.github.io/kwork-portfolio/)
