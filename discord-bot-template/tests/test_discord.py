"""Tests for Discord Bot Template."""
import ast, subprocess, pathlib

DIR = pathlib.Path(__file__).parent.parent

def test_bot_compiles():
    r = subprocess.run(["python", "-m", "py_compile", str(DIR / "bot.py")], capture_output=True)
    assert r.returncode == 0

def test_demo_runs():
    r = subprocess.run(["python", str(DIR / "demo.py")], capture_output=True, timeout=10)
    assert r.returncode == 0
    assert b"Discord" in r.stdout

def test_has_slash_commands():
    with open(DIR / "bot.py") as f:
        src = f.read()
    assert "@bot.tree.command" in src, "Missing slash commands"

def test_files_exist():
    for f in ["requirements.txt", "README.md", ".env.example", "Dockerfile", "Makefile"]:
        assert (DIR / f).exists(), f"Missing {f}"
