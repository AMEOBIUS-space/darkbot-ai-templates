import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from validator import ConfigValidator, ValidationReport


def test_define_schema():
    v = ConfigValidator()
    v.define_schema("app", {"name": {"type": "string", "required": True}})
    assert "app" in v.schemas


def test_valid_config():
    v = ConfigValidator()
    v.define_schema("app", {
        "name": {"type": "string", "required": True},
        "port": {"type": "integer", "required": True, "min": 1, "max": 65535},
    })
    report = v.validate("app", {"name": "myapp", "port": 8080})
    assert report.valid
    assert len(report.errors) == 0


def test_missing_required():
    v = ConfigValidator()
    v.define_schema("app", {"name": {"type": "string", "required": True}})
    report = v.validate("app", {})
    assert not report.valid
    assert any("Required" in e.message for e in report.errors)


def test_wrong_type():
    v = ConfigValidator()
    v.define_schema("app", {"port": {"type": "integer", "required": True}})
    report = v.validate("app", {"port": "not_a_number"})
    assert not report.valid
    assert any("Expected type" in e.message for e in report.errors)


def test_choices():
    v = ConfigValidator()
    v.define_schema("app", {"env": {"type": "string", "choices": ["dev", "prod", "staging"]}})
    report = v.validate("app", {"env": "invalid"})
    assert not report.valid
    assert any("choices" in e.message for e in report.errors)


def test_min_max():
    v = ConfigValidator()
    v.define_schema("app", {"port": {"type": "integer", "min": 1, "max": 65535}})
    r1 = v.validate("app", {"port": 0})
    assert not r1.valid
    r2 = v.validate("app", {"port": 99999})
    assert not r2.valid
    r3 = v.validate("app", {"port": 8080})
    assert r3.valid


def test_pattern():
    v = ConfigValidator()
    v.define_schema("app", {"name": {"type": "string", "pattern": r"^[a-z_]+$"}})
    r1 = v.validate("app", {"name": "my_app"})
    assert r1.valid
    r2 = v.validate("app", {"name": "My App!"})
    assert not r2.valid


def test_default_values():
    v = ConfigValidator()
    v.define_schema("app", {"debug": {"type": "boolean", "default": False}})
    report = v.validate("app", {})
    assert report.valid
    assert len(report.warnings) == 1


def test_load_defaults():
    v = ConfigValidator()
    v.define_schema("app", {
        "host": {"type": "string", "default": "localhost"},
        "port": {"type": "integer", "default": 8080},
    })
    defaults = v.load_defaults("app")
    assert defaults["host"] == "localhost"
    assert defaults["port"] == 8080


def test_env_validation():
    v = ConfigValidator()
    v.define_schema("app", {
        "port": {"type": "integer", "required": True, "env": "APP_PORT"},
        "debug": {"type": "boolean", "default": False, "env": "APP_DEBUG"},
    })
    env = {"APP_PORT": "3000", "APP_DEBUG": "true"}
    report = v.validate_env("app", env)
    assert report.valid


def test_env_coercion_integer():
    v = ConfigValidator()
    v.define_schema("app", {"port": {"type": "integer", "required": True}})
    report = v.validate_env("app", {"PORT": "8080"})
    assert report.valid


def test_string_length():
    v = ConfigValidator()
    v.define_schema("app", {"name": {"type": "string", "min_length": 3, "max_length": 10}})
    r1 = v.validate("app", {"name": "ab"})
    assert not r1.valid
    r2 = v.validate("app", {"name": "a" * 11})
    assert not r2.valid
    r3 = v.validate("app", {"name": "valid"})
    assert r3.valid


def test_schema_not_found():
    v = ConfigValidator()
    report = v.validate("nonexistent", {})
    assert not report.valid
    assert any("not found" in e.message for e in report.errors)


def test_boolean_type():
    v = ConfigValidator()
    v.define_schema("app", {"debug": {"type": "boolean"}})
    r1 = v.validate("app", {"debug": True})
    assert r1.valid
    r2 = v.validate("app", {"debug": "yes"})
    assert not r2.valid
