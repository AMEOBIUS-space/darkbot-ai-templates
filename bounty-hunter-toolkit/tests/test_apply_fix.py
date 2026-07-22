"""Tests for the Bounty Hunter Toolkit fix-application logic."""

import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPT = REPO_ROOT / "apply_fix.py"

sys.path.insert(0, str(REPO_ROOT))

from apply_fix import (  # noqa: E402
    PatternMatcher,
    PatternNotFoundError,
    UnknownPatternError,
    all_patterns,
    apply_fix,
    main,
)


def run_cli(*args: str) -> subprocess.CompletedProcess:
    """Invoke apply_fix.py as a subprocess and capture its output."""
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        capture_output=True,
        text=True,
    )


# --- CLI-level tests -------------------------------------------------------


def test_list_patterns_cli():
    r = run_cli("--list")
    assert r.returncode == 0
    assert "sql_injection" in r.stdout
    assert "zero_amount" in r.stdout
    assert "reentrancy" in r.stdout


def test_apply_sql_injection_cli(tmp_path):
    f = tmp_path / "app.py"
    f.write_text('cursor.execute(f"SELECT * FROM users WHERE name = \'{name}\'")')
    r = run_cli("--pattern", "sql_injection", "--file", str(f))
    assert r.returncode == 0
    assert "?" in f.read_text()
    assert 'f"' not in f.read_text()


def test_apply_xxe_cli(tmp_path):
    f = tmp_path / "app.py"
    f.write_text("import xml.etree.ElementTree as ET")
    r = run_cli("--pattern", "xxe", "--file", str(f))
    assert r.returncode == 0
    assert "defusedxml" in f.read_text()


def test_pattern_not_found_cli(tmp_path):
    f = tmp_path / "app.py"
    f.write_text("print('hello')")
    r = run_cli("--pattern", "sql_injection", "--file", str(f))
    assert r.returncode == 1


def test_unknown_pattern_cli(tmp_path):
    f = tmp_path / "app.py"
    f.write_text("print('hello')")
    r = run_cli("--pattern", "nonexistent", "--file", str(f))
    assert r.returncode == 1


def test_no_args_prints_help_and_fails():
    r = run_cli()
    assert r.returncode == 1
    assert "usage" in (r.stdout + r.stderr).lower()


def test_missing_file_cli():
    r = run_cli("--pattern", "sql_injection", "--file", "/nonexistent/path.py")
    assert r.returncode == 1
    assert "not found" in r.stderr.lower()


# --- Function-level tests --------------------------------------------------


def test_all_patterns_merge():
    patterns = all_patterns()
    assert "sql_injection" in patterns
    assert "reentrancy" in patterns
    assert patterns["sql_injection"].lang == "python"
    assert patterns["reentrancy"].lang == "solidity"


def test_apply_fix_returns_zero(tmp_path):
    f = tmp_path / "conf.yaml"
    f.write_text("data = yaml.load(data)")
    assert apply_fix("yaml_rce", f) == 0
    assert "safe_load" in f.read_text()


def test_apply_fix_unknown_pattern_raises(tmp_path):
    f = tmp_path / "app.py"
    f.write_text("print('hello')")
    with pytest.raises(UnknownPatternError):
        apply_fix("does_not_exist", f)


def test_apply_fix_pattern_not_found_raises(tmp_path):
    f = tmp_path / "app.py"
    f.write_text("print('hello')")
    with pytest.raises(PatternNotFoundError):
        apply_fix("sql_injection", f)


def test_apply_fix_missing_file_raises(tmp_path):
    with pytest.raises(FileNotFoundError):
        apply_fix("sql_injection", tmp_path / "missing.py")


def test_main_list_returns_zero(capsys):
    assert main(["--list"]) == 0
    out = capsys.readouterr().out
    assert "Python patterns" in out


def test_main_unknown_pattern_returns_one(tmp_path, capsys):
    f = tmp_path / "app.py"
    f.write_text("print('hi')")
    assert main(["--pattern", "nope", "--file", str(f)]) == 1


def test_main_find_patterns(capsys):
    assert main(["--find", "jwt"]) == 0
    out = capsys.readouterr().out
    assert "jwt_none" in out


def test_main_find_no_match(capsys):
    assert main(["--find", "xyzabc123"]) == 0
    assert capsys.readouterr().out == ""


def test_main_apply_alias_cli(tmp_path):
    f = tmp_path / "app.py"
    f.write_text('cursor.execute(f"SELECT * FROM users WHERE name = \'{name}\'")')
    assert main(["--apply", "sql_injection", "--file", str(f)]) == 0
    assert "?" in f.read_text()


def test_main_io_error_returns_one(tmp_path, monkeypatch, capsys):
    f = tmp_path / "app.py"
    f.write_text('cursor.execute(f"SELECT * FROM users WHERE name = \'{name}\'")')

    def raise_oserror(*args: object, **kwargs: object) -> None:
        raise OSError("disk full")

    monkeypatch.setattr("pathlib.Path.write_text", raise_oserror)
    assert main(["--pattern", "sql_injection", "--file", str(f)]) == 1
    assert "disk full" in capsys.readouterr().err


def test_pattern_matcher_find_by_name():
    matcher = PatternMatcher()
    matches = matcher.find("sql injection")
    assert any(p.name == "sql_injection" for p in matches)


def test_pattern_matcher_find_no_match():
    matcher = PatternMatcher()
    assert matcher.find("xyzabc123") == []


@pytest.mark.parametrize("pattern_name", list(all_patterns().keys()))
def test_apply_fix_all_patterns(pattern_name, tmp_path):
    pattern = all_patterns()[pattern_name]
    ext = "py" if pattern.lang == "python" else "sol"
    f = tmp_path / f"vuln.{ext}"
    f.write_text(pattern.bad)
    assert apply_fix(pattern_name, f) == 0
    content = f.read_text()
    assert pattern.good in content
    assert content != pattern.bad
