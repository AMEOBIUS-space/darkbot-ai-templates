#!/usr/bin/env python3
"""Demo: Config Validator."""
import sys, os, json
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))
from validator import ConfigValidator

v = ConfigValidator()
v.define_schema("server", {
    "host": {"type": "string", "required": True, "default": "localhost", "pattern": r"^[a-zA-Z0-9._-]+$"},
    "port": {"type": "integer", "required": True, "min": 1, "max": 65535, "default": 8080},
    "debug": {"type": "boolean", "default": False},
    "env": {"type": "string", "choices": ["dev", "staging", "prod"], "required": True},
    "workers": {"type": "integer", "min": 1, "max": 32, "default": 4},
    "secret_key": {"type": "string", "required": True, "min_length": 16},
})

# Valid config
print("=== Valid Config ===")
report = v.validate("server", {"host": "api.example.com", "port": 443, "debug": False, "env": "prod", "workers": 8, "secret_key": "a" * 32})
print(f"Valid: {report.valid} | Errors: {len(report.errors)} | Warnings: {len(report.warnings)}")

# Invalid config
print("\n=== Invalid Config ===")
report = v.validate("server", {"host": "bad host!", "port": 99999, "debug": "yes", "env": "invalid", "secret_key": "short"})
print(f"Valid: {report.valid}")
for e in report.errors:
    print(f"  [{e.field}] {e.message}")

# Defaults
print(f"\n=== Defaults ===\n{json.dumps(v.load_defaults('server'), indent=2)}")

# Env validation
print("\n=== Env Validation ===")
report = v.validate_env("server", {"HOST": "localhost", "PORT": "3000", "DEBUG": "false", "ENV": "dev", "SECRET_KEY": "s" * 20})
print(f"Valid: {report.valid}")
