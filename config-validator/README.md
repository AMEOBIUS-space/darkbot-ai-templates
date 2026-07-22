# Config Validator

> Schema-based validation for JSON, YAML, TOML, and environment configs

## Features

- Type validation (string, integer, float, boolean, list, dict)
- Required fields + default values
- Min/max for numbers, min_length/max_length for strings
- Regex pattern matching
- Enum choices validation
- Environment variable validation with type coercion
- JSON file validation
- Default values generation
- Detailed error reports (field, expected, actual)

## Quick Start

```python
from validator import ConfigValidator

v = ConfigValidator()
v.define_schema("app", {
    "port": {"type": "integer", "required": True, "min": 1, "max": 65535},
    "env": {"type": "string", "choices": ["dev", "prod"]},
})
report = v.validate("app", {"port": 8080, "env": "prod"})
print(f"Valid: {report.valid}")
```

## Tests

```bash
python -m pytest tests/ -v
```

## License

MIT

Freelance portfolio: [https://ameobius-space.github.io/kwork-portfolio/](https://ameobius-space.github.io/kwork-portfolio/)
