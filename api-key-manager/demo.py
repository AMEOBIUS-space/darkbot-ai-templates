#!/usr/bin/env python3
"""Demo: API Key Manager."""
import sys, os, json
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))
from key_manager import APIKeyManager

mgr = APIKeyManager(master_secret="my_app_secret")

# Create keys with different scopes
raw1, key1 = mgr.create_key(scopes=["read", "write"], rate_limit=100, description="Mobile App")
raw2, key2 = mgr.create_key(scopes=["admin"], rate_limit=1000, description="Admin Dashboard")
raw3, key3 = mgr.create_key(scopes=["read"], rate_limit=10, description="Public API")

print("=== Created 3 API Keys ===")
for k in mgr.list_keys():
    print(f"  {k['prefix']} | scopes={k['scopes']} | limit={k['rate_limit']}/min | {k['description']}")

# Validate
print("\n=== Validation ===")
valid, key, msg = mgr.validate_key(raw1)
print(f"  Key 1: valid={valid} scopes={key.scopes if key else '?'}")

valid, key, msg = mgr.validate_key("dk_invalid")
print(f"  Invalid: valid={valid} msg={msg}")

# Scope check
print("\n=== Scope Check ===")
print(f"  Key 1 can write: {mgr.check_scope(key1, 'write')}")
print(f"  Key 1 can delete: {mgr.check_scope(key1, 'delete')}")
print(f"  Key 2 (admin) can delete: {mgr.check_scope(key2, 'delete')}")

# Rotate
print("\n=== Rotation ===")
new_raw, new_key = mgr.rotate_key(key1.key_id)
valid_old, _, _ = mgr.validate_key(raw1)
valid_new, _, _ = mgr.validate_key(new_raw)
print(f"  Old key valid: {valid_old} (should be False)")
print(f"  New key valid: {valid_new} (should be True)")

print(f"\nStats: {json.dumps(mgr.stats(), indent=2)}")
