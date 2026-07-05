"""Tests for TG Bot Template — verify structure and demo."""
import ast
import subprocess
import os
import pathlib

TEMPLATE_DIR = pathlib.Path(__file__).parent.parent

def test_bot_py_compiles():
    """bot.py must compile without syntax errors."""
    r = subprocess.run(
        ["python", "-m", "py_compile", str(TEMPLATE_DIR / "bot.py")],
        capture_output=True
    )
    assert r.returncode == 0, f"py_compile failed: {r.stderr.decode()}"

def test_demo_py_compiles():
    """demo.py must compile."""
    r = subprocess.run(
        ["python", "-m", "py_compile", str(TEMPLATE_DIR / "demo.py")],
        capture_output=True
    )
    assert r.returncode == 0

def test_demo_runs():
    """demo.py must run without errors."""
    r = subprocess.run(
        ["python", str(TEMPLATE_DIR / "demo.py")],
        capture_output=True, timeout=10
    )
    assert r.returncode == 0
    assert b"DarkBot AI" in r.stdout

def test_requirements_exists():
    """requirements.txt must exist."""
    assert (TEMPLATE_DIR / "requirements.txt").exists()

def test_readme_exists():
    """README.md must exist."""
    assert (TEMPLATE_DIR / "README.md").exists()

def test_env_example_exists():
    """ .env.example must exist."""
    assert (TEMPLATE_DIR / ".env.example").exists()

def test_dockerfile_exists():
    """Dockerfile must exist."""
    assert (TEMPLATE_DIR / "Dockerfile").exists()

def test_makefile_exists():
    """Makefile must exist."""
    assert (TEMPLATE_DIR / "Makefile").exists()

def test_bot_has_handlers():
    """bot.py must have command handlers."""
    with open(TEMPLATE_DIR / "bot.py") as f:
        tree = ast.parse(f.read())
    funcs = [n.name for n in ast.walk(tree) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]
    assert "start" in funcs or any("start" in f for f in funcs), "Missing start handler"
