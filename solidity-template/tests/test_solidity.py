import subprocess, pathlib
DIR = pathlib.Path(__file__).parent.parent
def test_contract_exists():
    assert (DIR/"contracts/Token.sol").exists()
def test_demo_runs():
    r = subprocess.run(["python",str(DIR/"demo.py")],capture_output=True,timeout=10)
    assert r.returncode == 0
    assert b"Solidity" in r.stdout or b"ERC20" in r.stdout
def test_foundry_config():
    assert (DIR/"foundry.toml").exists()
def test_deploy_script():
    assert (DIR/"script/Deploy.s.sol").exists()
def test_files_exist():
    for f in ["requirements.txt","README.md","Makefile"]:
        assert (DIR/f).exists()
