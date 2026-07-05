"""Tests for FastAPI Template — verify structure and demo."""
import ast, subprocess, pathlib

TEMPLATE_DIR = pathlib.Path(__file__).parent.parent

def test_main_compiles():
    r = subprocess.run(["python", "-m", "py_compile", str(TEMPLATE_DIR / "main.py")], capture_output=True)
    assert r.returncode == 0

def test_demo_compiles():
    r = subprocess.run(["python", "-m", "py_compile", str(TEMPLATE_DIR / "demo.py")], capture_output=True)
    assert r.returncode == 0

def test_demo_runs():
    r = subprocess.run(["python", str(TEMPLATE_DIR / "demo.py")], capture_output=True, timeout=10)
    assert r.returncode == 0
    assert b"FastAPI" in r.stdout

def test_has_endpoints():
    with open(TEMPLATE_DIR / "main.py") as f:
        tree = ast.parse(f.read())
    funcs = [n.name for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)]
    assert "register" in funcs, "Missing register endpoint"
    assert "login" in funcs, "Missing login endpoint"
    assert "create_item" in funcs, "Missing create_item endpoint"

def test_files_exist():
    for f in ["requirements.txt", "README.md", ".env.example", "Dockerfile", "Makefile"]:
        assert (TEMPLATE_DIR / f).exists(), f"Missing {f}"
