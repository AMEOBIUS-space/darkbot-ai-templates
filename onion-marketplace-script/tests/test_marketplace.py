import subprocess, pathlib, ast
DIR = pathlib.Path(__file__).parent.parent
def test_marketplace_compiles():
    r = subprocess.run(["python","-m","py_compile",str(DIR/"marketplace.py")],capture_output=True)
    assert r.returncode == 0
def test_demo_runs():
    r = subprocess.run(["python",str(DIR/"demo.py")],capture_output=True,timeout=10)
    assert r.returncode == 0
    assert b"Marketplace" in r.stdout or b"onion" in r.stdout
def test_has_classes():
    with open(DIR/"marketplace.py") as f:
        tree = ast.parse(f.read())
    classes = [n.name for n in ast.walk(tree) if isinstance(n, ast.ClassDef)]
    assert "Listing" in classes and "OnionMarketplace" in classes
def test_files_exist():
    for f in ["requirements.txt","README.md",".env.example","Dockerfile","Makefile"]:
        assert (DIR/f).exists()
