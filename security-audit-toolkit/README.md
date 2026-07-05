# Security Audit Toolkit

> OWASP Top 10 vulnerability scanner for Python code — 12 detection rules

## Rules

| ID | Vulnerability | Severity |
|---|---|---|
| SQLI-001 | SQL Injection (f-string) | CRITICAL |
| SQLI-002 | SQL Injection (concatenation) | CRITICAL |
| XSS-001 | XSS (template) | HIGH |
| HARDCODE-001 | Hardcoded secret | HIGH |
| JWT-001 | JWT no algorithm | HIGH |
| XXE-001 | XML External Entity | HIGH |
| YAML-001 | Unsafe YAML load | CRITICAL |
| PICKLE-001 | Unsafe pickle | CRITICAL |
| REDIRECT-001 | Open Redirect | MEDIUM |
| DEBUG-001 | Debug mode | MEDIUM |
| EVAL-001 | Code injection (eval) | CRITICAL |
| SHELL-001 | Shell injection | CRITICAL |

## Quick Start

```python
from scanner import SecurityScanner

scanner = SecurityScanner()
vulns = scanner.scan_file("app.py")
for v in vulns:
    print(f"[{v.severity}] {v.title} at line {v.line}")
    print(f"  Fix: {v.fix}")
```

## Tests

```bash
python -m pytest tests/ -v
```

## License

MIT
