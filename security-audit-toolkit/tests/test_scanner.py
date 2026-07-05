import sys, os, tempfile
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from scanner import SecurityScanner, Vulnerability


def test_scan_clean_code():
    scanner = SecurityScanner()
    with tempfile.NamedTemporaryFile(suffix=".py", mode="w", delete=False) as f:
        f.write("x = 1 + 2\nprint(x)\n")
        f.flush()
        result = scanner.scan_file(f.name)
    os.unlink(f.name)
    assert len(result) == 0


def test_scan_sql_injection():
    scanner = SecurityScanner()
    with tempfile.NamedTemporaryFile(suffix=".py", mode="w", delete=False) as f:
        f.write('cursor.execute(f"SELECT * FROM users WHERE id = {user_id}")\n')
        f.flush()
        result = scanner.scan_file(f.name)
    os.unlink(f.name)
    assert any(v.rule_id == "SQLI-001" for v in result)
    assert any(v.severity == "CRITICAL" for v in result)


def test_scan_hardcoded_secret():
    scanner = SecurityScanner()
    with tempfile.NamedTemporaryFile(suffix=".py", mode="w", delete=False) as f:
        f.write('password = "supersecret123"\n')
        f.flush()
        result = scanner.scan_file(f.name)
    os.unlink(f.name)
    assert any(v.rule_id == "HARDCODE-001" for v in result)


def test_scan_yaml_rce():
    scanner = SecurityScanner()
    with tempfile.NamedTemporaryFile(suffix=".py", mode="w", delete=False) as f:
        f.write("import yaml\ndata = yaml.load(f)\n")
        f.flush()
        result = scanner.scan_file(f.name)
    os.unlink(f.name)
    assert any(v.rule_id == "YAML-001" for v in result)


def test_scan_eval():
    scanner = SecurityScanner()
    with tempfile.NamedTemporaryFile(suffix=".py", mode="w", delete=False) as f:
        f.write("result = eval(user_input)\n")
        f.flush()
        result = scanner.scan_file(f.name)
    os.unlink(f.name)
    assert any(v.rule_id == "EVAL-001" for v in result)


def test_scan_xxe():
    scanner = SecurityScanner()
    with tempfile.NamedTemporaryFile(suffix=".py", mode="w", delete=False) as f:
        f.write("import xml.etree.ElementTree as ET\n")
        f.flush()
        result = scanner.scan_file(f.name)
    os.unlink(f.name)
    assert any(v.rule_id == "XXE-001" for v in result)


def test_scan_debug_mode():
    scanner = SecurityScanner()
    with tempfile.NamedTemporaryFile(suffix=".py", mode="w", delete=False) as f:
        f.write("app.run(debug=True)\n")
        f.flush()
        result = scanner.scan_file(f.name)
    os.unlink(f.name)
    assert any(v.rule_id == "DEBUG-001" for v in result)


def test_report_summary():
    scanner = SecurityScanner()
    with tempfile.NamedTemporaryFile(suffix=".py", mode="w", delete=False) as f:
        f.write('eval(input())\nyaml.load(f)\n')
        f.flush()
        scanner.scan_file(f.name)
    os.unlink(f.name)
    summary = scanner.report_summary()
    assert summary["total_vulnerabilities"] >= 2
    assert "CRITICAL" in summary["by_severity"]


def test_report_json():
    scanner = SecurityScanner()
    with tempfile.NamedTemporaryFile(suffix=".py", mode="w", delete=False) as f:
        f.write("eval(x)\n")
        f.flush()
        scanner.scan_file(f.name)
    os.unlink(f.name)
    import json
    report = json.loads(scanner.report_json())
    assert len(report) >= 1
    assert "rule_id" in report[0]


def test_scan_nonexistent_file():
    scanner = SecurityScanner()
    result = scanner.scan_file("/nonexistent/path.py")
    assert result == []


def test_fix_suggestion():
    scanner = SecurityScanner()
    with tempfile.NamedTemporaryFile(suffix=".py", mode="w", delete=False) as f:
        f.write("os.system('ls')\n")
        f.flush()
        result = scanner.scan_file(f.name)
    os.unlink(f.name)
    assert any("subprocess" in v.fix for v in result)
