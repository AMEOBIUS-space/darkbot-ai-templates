"""Tests for Crypto Trading Bot Template."""
import ast, subprocess, pathlib

DIR = pathlib.Path(__file__).parent.parent

def test_bot_compiles():
    r = subprocess.run(["python", "-m", "py_compile", str(DIR / "bot.py")], capture_output=True)
    assert r.returncode == 0

def test_demo_runs():
    r = subprocess.run(["python", str(DIR / "demo.py")], capture_output=True, timeout=15)
    assert r.returncode == 0
    assert b"RSI" in r.stdout or b"Trading" in r.stdout

def test_has_classes():
    with open(DIR / "bot.py") as f:
        tree = ast.parse(f.read())
    classes = [n.name for n in ast.walk(tree) if isinstance(n, ast.ClassDef)]
    assert "TradingBot" in classes, "Missing TradingBot class"

def test_files_exist():
    for f in ["requirements.txt", "README.md", ".env.example", "Dockerfile", "Makefile"]:
        assert (DIR / f).exists(), f"Missing {f}"
