"""Security Audit Toolkit — OWASP Top 10 vulnerability scanner for Python code."""
import re
import ast
import json
from typing import List, Dict, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path


@dataclass
class Vulnerability:
    rule_id: str
    owasp_category: str
    severity: str  # CRITICAL, HIGH, MEDIUM, LOW
    title: str
    description: str
    file: str
    line: int
    code_snippet: str
    fix: str


class SecurityScanner:
    """Static analysis scanner for OWASP Top 10 vulnerabilities in Python code."""

    RULES = {
        "SQLI-001": {
            "owasp": "A03:2021 - Injection",
            "severity": "CRITICAL",
            "title": "SQL Injection — f-string in query",
            "pattern": r'execute\s*\(\s*f["\']',
            "fix": "Use parameterized queries: cursor.execute('SELECT * FROM t WHERE id = ?', (id,))",
        },
        "SQLI-002": {
            "owasp": "A03:2021 - Injection",
            "severity": "CRITICAL",
            "title": "SQL Injection — string concatenation in query",
            "pattern": r'execute\s*\(\s*["\'].*?\+\s*',
            "fix": "Use parameterized queries with ? placeholders",
        },
        "XSS-001": {
            "owasp": "A03:2021 - Injection",
            "severity": "HIGH",
            "title": "XSS — unescaped output in template",
            "pattern": r'render_template_string\s*\(\s*f["\']',
            "fix": "Use Jinja2 variables: render_template_string('Hello {{ name }}', name=user_input)",
        },
        "HARDCODE-001": {
            "owasp": "A07:2021 - Security Misconfiguration",
            "severity": "HIGH",
            "title": "Hardcoded secret",
            "pattern": r'(password|secret|api_key|token)\s*=\s*["\'][^"\']{8,}["\']',
            "fix": "Use environment variables: os.getenv('API_KEY')",
        },
        "JWT-001": {
            "owasp": "A02:2021 - Cryptographic Failures",
            "severity": "HIGH",
            "title": "JWT — no algorithm specified",
            "pattern": r'jwt\.decode\s*\([^)]*algorithms\s*=\s*None',
            "fix": "Specify algorithms: jwt.decode(token, key, algorithms=['HS256'])",
        },
        "XXE-001": {
            "owasp": "A05:2021 - Security Misconfiguration",
            "severity": "HIGH",
            "title": "XXE — unsafe XML parsing",
            "pattern": r'import\s+xml\.etree\.ElementTree',
            "fix": "Use defusedxml: import defusedxml.ElementTree as DET",
        },
        "YAML-001": {
            "owasp": "A08:2021 - Software and Data Integrity Failures",
            "severity": "CRITICAL",
            "title": "Unsafe YAML load (RCE risk)",
            "pattern": r'yaml\.load\s*\(',
            "fix": "Use yaml.safe_load() instead of yaml.load()",
        },
        "PICKLE-001": {
            "owasp": "A08:2021 - Software and Data Integrity Failures",
            "severity": "CRITICAL",
            "title": "Unsafe pickle deserialization (RCE risk)",
            "pattern": r'pickle\.loads?\s*\(',
            "fix": "Use JSON or restricted unpickler",
        },
        "REDIRECT-001": {
            "owasp": "A01:2021 - Broken Access Control",
            "severity": "MEDIUM",
            "title": "Open Redirect — unvalidated redirect",
            "pattern": r'redirect\s*\(\s*request\.(args|form|json)',
            "fix": "Validate URL is same-origin: urlparse + check netloc",
        },
        "DEBUG-001": {
            "owasp": "A05:2021 - Security Misconfiguration",
            "severity": "MEDIUM",
            "title": "Debug mode enabled",
            "pattern": r'debug\s*=\s*True',
            "fix": "Set debug=False in production",
        },
        "EVAL-001": {
            "owasp": "A03:2021 - Injection",
            "severity": "CRITICAL",
            "title": "Code injection via eval()",
            "pattern": r'\beval\s*\(',
            "fix": "Use ast.literal_eval() for safe evaluation",
        },
        "SHELL-001": {
            "owasp": "A03:2021 - Injection",
            "severity": "CRITICAL",
            "title": "Shell injection via os.system",
            "pattern": r'os\.system\s*\(',
            "fix": "Use subprocess.run with shell=False and argument list",
        },
    }

    def __init__(self):
        self.vulnerabilities: List[Vulnerability] = []

    def scan_file(self, filepath: str) -> List[Vulnerability]:
        """Scan a single Python file for vulnerabilities."""
        path = Path(filepath)
        if not path.exists() or path.suffix != ".py":
            return []

        content = path.read_text()
        lines = content.splitlines()
        found = []

        for rule_id, rule in self.RULES.items():
            for match in re.finditer(rule["pattern"], content, re.IGNORECASE):
                line_num = content[:match.start()].count("\n") + 1
                snippet = lines[line_num - 1].strip() if line_num <= len(lines) else ""
                vuln = Vulnerability(
                    rule_id=rule_id,
                    owasp_category=rule["owasp"],
                    severity=rule["severity"],
                    title=rule["title"],
                    description=f"Pattern '{rule['pattern']}' matched at line {line_num}",
                    file=str(filepath),
                    line=line_num,
                    code_snippet=snippet[:100],
                    fix=rule["fix"],
                )
                found.append(vuln)
                self.vulnerabilities.append(vuln)

        return found

    def scan_directory(self, dirpath: str) -> List[Vulnerability]:
        """Scan all Python files in a directory."""
        base = Path(dirpath)
        all_found = []
        for py_file in base.rglob("*.py"):
            found = self.scan_file(str(py_file))
            all_found.extend(found)
        return all_found

    def report_json(self) -> str:
        """Generate JSON report."""
        return json.dumps([asdict(v) for v in self.vulnerabilities], indent=2)

    def report_summary(self) -> Dict:
        """Generate summary statistics."""
        by_severity = {}
        by_owasp = {}
        for v in self.vulnerabilities:
            by_severity[v.severity] = by_severity.get(v.severity, 0) + 1
            by_owasp[v.owasp_category] = by_owasp.get(v.owasp_category, 0) + 1
        return {
            "total_vulnerabilities": len(self.vulnerabilities),
            "by_severity": by_severity,
            "by_owasp": by_owasp,
            "files_scanned": len(set(v.file for v in self.vulnerabilities)),
        }
