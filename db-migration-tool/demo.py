#!/usr/bin/env python3
"""Demo: Database Migration Tool."""
import sys, os, json
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))
from migrations import MigrationManager

mgr = MigrationManager()

mgr.add("001", "create_users", "CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT, email TEXT)", "DROP TABLE users")
mgr.add("002", "add_timestamps", "ALTER TABLE users ADD COLUMN created_at TEXT; ALTER TABLE users ADD COLUMN updated_at TEXT", "")
mgr.add("003", "add_posts", "CREATE TABLE posts (id INTEGER PRIMARY KEY, user_id INTEGER, title TEXT, content TEXT)", "DROP TABLE posts")
mgr.add("004", "add_indexes", "CREATE INDEX idx_users_email ON users(email); CREATE INDEX idx_posts_user ON posts(user_id)", "DROP INDEX idx_users_email; DROP INDEX idx_posts_user")

print("=== Before Migration ===")
print(json.dumps(mgr.status(), indent=2))

print("\n=== Migrating UP to 003 ===")
count, applied = mgr.migrate_up(target_version="003")
print(f"Applied: {applied}")

print("\n=== Migrating UP (all) ===")
count, applied = mgr.migrate_up()
print(f"Applied: {applied}")

print("\n=== Status ===")
print(json.dumps(mgr.status(), indent=2))

print("\n=== Verify Checksums ===")
mismatches = mgr.verify_checksums()
print(f"Mismatches: {mismatches}")

print("\n=== Rollback 1 step ===")
count, rolled = mgr.migrate_down(steps=1)
print(f"Rolled back: {rolled}")

print(f"\nFinal version: {mgr.current_version()}")
