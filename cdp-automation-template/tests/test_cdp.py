import ast, subprocess, pathlib
DIR = pathlib.Path(__file__).parent.parent
def test_cdp_compiles():
    r = subprocess.run(["python", "-m", "py_compile", str(DIR/"cdp_agent.py")], capture_output=True)
    assert r.returncode == 0
def test_demo_runs():
    r = subprocess.run(["python", str(DIR/"demo.py")], capture_output=True, timeout=10)
    assert r.returncode == 0
    assert b"CDP" in r.stdout
def test_files_exist():
    for f in ["requirements.txt","README.md",".env.example","Dockerfile","Makefile"]:
        assert (DIR/f).exists()
