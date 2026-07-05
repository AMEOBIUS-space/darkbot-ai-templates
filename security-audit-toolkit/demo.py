#!/usr/bin/env python3
"""Demo: Security Audit Toolkit — scan vulnerable code."""
import sys, os, tempfile
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))
from scanner import SecurityScanner

vuln_code = """
import yaml
import xml.etree.ElementTree as ET
import pickle

password = "supersecret123"
cursor.execute(f"SELECT * FROM users WHERE id = {user_id}")
result = eval(user_input)
os.system(user_input)
app.run(debug=True)
"""

with tempfile.NamedTemporaryFile(suffix=".py", mode="w", delete=False) as f:
    f.write(vuln_code)
    f.flush()
    scanner = SecurityScanner()
    vulns = scanner.scan_file(f.name)
os.unlink(f.name)

print(f"=== Found {len(vulns)} vulnerabilities ===\n")
for v in vulns:
    print(f"[{v.severity}] {v.rule_id}: {v.title}")
    print(f"  Line {v.line}: {v.code_snippet}")
    print(f"  Fix: {v.fix}")
    print()

print(f"Summary: {scanner.report_summary()}")
