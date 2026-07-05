"""Config Validator — schema-based validation for YAML, JSON, TOML, and env configs."""
import json
import os
import re
from typing import Dict, List, Optional, Any, Union, Tuple
from dataclasses import dataclass, asdict, field
from pathlib import Path


@dataclass
class ValidationError:
    field: str
    message: str
    severity: str = "error"  # error, warning
    expected: str = ""
    actual: str = ""


@dataclass
class ValidationReport:
    valid: bool
    errors: List[ValidationError] = field(default_factory=list)
    warnings: List[ValidationError] = field(default_factory=list)
    checked_fields: int = 0


class ConfigValidator:
    """Validate configuration files against a schema definition."""

    TYPE_MAP = {
        "string": str,
        "integer": int,
        "float": (int, float),
        "boolean": bool,
        "list": list,
        "dict": dict,
    }

    def __init__(self):
        self.schemas: Dict[str, Dict] = {}

    def define_schema(self, name: str, schema: Dict):
        """Define a config schema.

        Schema format:
        {
            "field_name": {
                "type": "string",
                "required": True,
                "default": "hello",
                "min": 1,
                "max": 100,
                "pattern": r"^[a-z]+$",
                "choices": ["a", "b", "c"],
                "env": "FIELD_NAME",  # Override env var name
            }
        }
        """
        self.schemas[name] = schema

    def validate(self, schema_name: str, config: Dict, source: str = "config") -> ValidationReport:
        """Validate a config dict against a named schema."""
        schema = self.schemas.get(schema_name)
        if not schema:
            return ValidationReport(valid=False, errors=[
                ValidationError(field="_schema", message=f"Schema '{schema_name}' not found")
            ])

        errors = []
        warnings = []
        checked = 0

        for field_name, rules in schema.items():
            checked += 1
            value = config.get(field_name)
            field_path = f"{source}.{field_name}"

            # Check required
            if rules.get("required", False) and value is None:
                errors.append(ValidationError(
                    field=field_path, message="Required field missing",
                    expected="present", actual="missing"
                ))
                continue

            # Apply default if missing
            if value is None and "default" in rules:
                value = rules["default"]
                warnings.append(ValidationError(
                    field=field_path, message=f"Using default value: {value}",
                    severity="warning"
                ))

            if value is None:
                continue

            # Type check
            expected_type = rules.get("type")
            if expected_type and expected_type in self.TYPE_MAP:
                py_type = self.TYPE_MAP[expected_type]
                if not isinstance(value, py_type):
                    errors.append(ValidationError(
                        field=field_path,
                        message=f"Expected type '{expected_type}', got '{type(value).__name__}'",
                        expected=expected_type, actual=type(value).__name__
                    ))
                    continue

            # Choices check
            if "choices" in rules and value not in rules["choices"]:
                errors.append(ValidationError(
                    field=field_path,
                    message=f"Value '{value}' not in allowed choices",
                    expected=str(rules["choices"]), actual=str(value)
                ))

            # Min/max for numeric
            if isinstance(value, (int, float)):
                if "min" in rules and value < rules["min"]:
                    errors.append(ValidationError(
                        field=field_path,
                        message=f"Value {value} below minimum {rules['min']}",
                        expected=f">= {rules['min']}", actual=str(value)
                    ))
                if "max" in rules and value > rules["max"]:
                    errors.append(ValidationError(
                        field=field_path,
                        message=f"Value {value} above maximum {rules['max']}",
                        expected=f"<= {rules['max']}", actual=str(value)
                    ))

            # Pattern for strings
            if isinstance(value, str) and "pattern" in rules:
                if not re.match(rules["pattern"], value):
                    errors.append(ValidationError(
                        field=field_path,
                        message=f"Value '{value}' does not match pattern {rules['pattern']}",
                        expected=rules["pattern"], actual=value
                    ))

            # Min/max length for strings
            if isinstance(value, str):
                if "min_length" in rules and len(value) < rules["min_length"]:
                    errors.append(ValidationError(
                        field=field_path,
                        message=f"String length {len(value)} below min {rules['min_length']}"
                    ))
                if "max_length" in rules and len(value) > rules["max_length"]:
                    errors.append(ValidationError(
                        field=field_path,
                        message=f"String length {len(value)} above max {rules['max_length']}"
                    ))

        return ValidationReport(
            valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            checked_fields=checked,
        )

    def validate_json_file(self, schema_name: str, filepath: str) -> ValidationReport:
        """Load and validate a JSON config file."""
        config = json.loads(Path(filepath).read_text())
        return self.validate(schema_name, config, filepath)

    def validate_env(self, schema_name: str, env: Dict = None) -> ValidationReport:
        """Validate environment variables against schema.
        Maps schema fields to env vars (uppercased or 'env' override)."""
        env = env or os.environ
        schema = self.schemas.get(schema_name, {})
        config = {}
        for field_name, rules in schema.items():
            env_key = rules.get("env", field_name.upper())
            if env_key in env:
                raw = env[env_key]
                # Type coercion
                field_type = rules.get("type", "string")
                if field_type == "integer":
                    try:
                        config[field_name] = int(raw)
                    except ValueError:
                        config[field_name] = raw  # Let validation catch it
                elif field_type == "float":
                    try:
                        config[field_name] = float(raw)
                    except ValueError:
                        config[field_name] = raw
                elif field_type == "boolean":
                    config[field_name] = raw.lower() in ("true", "1", "yes")
                elif field_type == "list":
                    config[field_name] = raw.split(",")
                else:
                    config[field_name] = raw
        return self.validate(schema_name, config, "env")

    def load_defaults(self, schema_name: str) -> Dict:
        """Generate config with all default values."""
        schema = self.schemas.get(schema_name, {})
        return {k: v.get("default") for k, v in schema.items() if "default" in v}
