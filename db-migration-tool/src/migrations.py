"""Database Migration Tool — versioned schema migrations with rollback support."""
import json
import sqlite3
import time
import hashlib
from typing import Dict, List, Optional, Tuple, Callable
from dataclasses import dataclass, asdict, field
from datetime import datetime
from pathlib import Path


@dataclass
class Migration:
    version: str
    name: str
    up_sql: str
    down_sql: str
    checksum: str = ""
    applied_at: str = ""


class MigrationManager:
    """Manage database schema migrations with versioning and rollback."""

    def __init__(self, db_path: str = ":memory:"):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self.migrations: Dict[str, Migration] = {}
        self.applied_versions: List[str] = []
        self._ensure_migrations_table()

    def _ensure_migrations_table(self):
        """Create the _migrations tracking table if it doesn't exist."""
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS _migrations (
                version TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                checksum TEXT NOT NULL,
                applied_at TEXT NOT NULL
            )
        """)
        self.conn.commit()
        self._load_applied()

    def _load_applied(self):
        """Load applied migrations from the database."""
        cursor = self.conn.execute("SELECT version FROM _migrations ORDER BY version")
        self.applied_versions = [row[0] for row in cursor.fetchall()]

    def _checksum(self, migration: Migration) -> str:
        content = f"{migration.version}:{migration.name}:{migration.up_sql}:{migration.down_sql}"
        return hashlib.sha256(content.encode()).hexdigest()[:16]

    def add(self, version: str, name: str, up_sql: str, down_sql: str):
        """Register a migration."""
        migration = Migration(version=version, name=name, up_sql=up_sql, down_sql=down_sql)
        migration.checksum = self._checksum(migration)
        self.migrations[version] = migration

    def add_from_file(self, version: str, name: str, filepath: str):
        """Load migration SQL from a file (expects -- UP -- and -- DOWN -- sections)."""
        content = Path(filepath).read_text()
        parts = content.split("-- DOWN --")
        up = parts[0].replace("-- UP --", "").strip()
        down = parts[1].strip() if len(parts) > 1 else ""
        self.add(version, name, up, down)

    def migrate_up(self, target_version: str = None) -> Tuple[int, List[str]]:
        """Apply migrations up to target_version (or all). Returns (count, applied_versions)."""
        sorted_versions = sorted(self.migrations.keys())
        if target_version:
            sorted_versions = [v for v in sorted_versions if v <= target_version]

        applied = []
        for version in sorted_versions:
            if version in self.applied_versions:
                continue
            migration = self.migrations[version]
            try:
                self.conn.executescript(migration.up_sql)
                self.conn.execute(
                    "INSERT INTO _migrations (version, name, checksum, applied_at) VALUES (?, ?, ?, ?)",
                    (version, migration.name, migration.checksum, datetime.now().isoformat())
                )
                self.conn.commit()
                migration.applied_at = datetime.now().isoformat()
                self.applied_versions.append(version)
                applied.append(version)
            except Exception as e:
                self.conn.rollback()
                raise RuntimeError(f"Migration {version} failed: {e}")
        return len(applied), applied

    def migrate_down(self, steps: int = 1) -> Tuple[int, List[str]]:
        """Rollback N migrations. Returns (count, rolled_back_versions)."""
        rolled_back = []
        for _ in range(steps):
            if not self.applied_versions:
                break
            version = self.applied_versions[-1]
            migration = self.migrations.get(version)
            if not migration or not migration.down_sql:
                break
            try:
                self.conn.executescript(migration.down_sql)
                self.conn.execute("DELETE FROM _migrations WHERE version = ?", (version,))
                self.conn.commit()
                self.applied_versions.remove(version)
                rolled_back.append(version)
            except Exception as e:
                self.conn.rollback()
                raise RuntimeError(f"Rollback {version} failed: {e}")
        return len(rolled_back), rolled_back

    def current_version(self) -> Optional[str]:
        """Get the current migration version."""
        return self.applied_versions[-1] if self.applied_versions else None

    def pending(self) -> List[str]:
        """Get list of pending migration versions."""
        return [v for v in sorted(self.migrations.keys()) if v not in self.applied_versions]

    def status(self) -> Dict:
        """Get migration status."""
        return {
            "current_version": self.current_version(),
            "total_migrations": len(self.migrations),
            "applied": len(self.applied_versions),
            "pending": len(self.pending()),
            "pending_versions": self.pending(),
            "applied_versions": self.applied_versions,
        }

    def verify_checksums(self) -> List[str]:
        """Verify migration checksums haven't been tampered with."""
        mismatches = []
        cursor = self.conn.execute("SELECT version, checksum FROM _migrations")
        for version, stored_checksum in cursor.fetchall():
            migration = self.migrations.get(version)
            if migration and migration.checksum != stored_checksum:
                mismatches.append(version)
        return mismatches

    def close(self):
        self.conn.close()
