import subprocess, sys, os
from pathlib import Path

def run(cmd):
    return subprocess.run(cmd, capture_output=True, text=True)

def test_list_patterns():
    r = run([sys.executable, "bounty-hunter-toolkit/apply_fix.py", "--list"])
    assert r.returncode == 0
    assert "sql_injection" in r.stdout
    assert "zero_amount" in r.stdout
    assert "reentrancy" in r.stdout

def test_apply_sql_injection(tmp_path):
    f = tmp_path / "app.py"
    f.write_text('cursor.execute(f"SELECT * FROM users WHERE name = \'{name}\'")')
    r = run([sys.executable, "bounty-hunter-toolkit/apply_fix.py", "--pattern", "sql_injection", "--file", str(f)])
    assert r.returncode == 0
    assert "?" in f.read_text()
    assert "f\"" not in f.read_text()

def test_apply_xxw(tmp_path):
    f = tmp_path / "app.py"
    f.write_text("import xml.etree.ElementTree as ET")
    r = run([sys.executable, "bounty-hunter-toolkit/apply_fix.py", "--pattern", "xxe", "--file", str(f)])
    assert r.returncode == 0
    assert "defusedxml" in f.read_text()

def test_pattern_not_found(tmp_path):
    f = tmp_path / "app.py"
    f.write_text("print('hello')")
    r = run([sys.executable, "bounty-hunter-toolkit/apply_fix.py", "--pattern", "sql_injection", "--file", str(f)])
    assert r.returncode == 1

def test_unknown_pattern(tmp_path):
    f = tmp_path / "app.py"
    f.write_text("print('hello')")
    r = run([sys.executable, "bounty-hunter-toolkit/apply_fix.py", "--pattern", "nonexistent", "--file", str(f)])
    assert r.returncode == 1
