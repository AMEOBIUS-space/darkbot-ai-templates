# Security Audit Toolkit

OWASP-oriented static scanner for Python — 12 regex rules covering injection, secrets, unsafe loaders, and misconfig.

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

## Quick start

```bash
python demo.py
# or
python -c "from src.scanner import SecurityScanner; print(SecurityScanner().scan_file('app.py'))"
```

Library usage:

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
python3 -m pytest tests/ -q
```

## Layout

- `src/scanner.py` — rules + scanner
- `demo.py` — offline smoke on synthetic vulns
- `tests/` — rule coverage

## License

MIT · AMEOBIUS-team

## Related

- https://github.com/AMEOBIUS-team/tor-hidden-service-template
- https://github.com/AMEOBIUS-team/bounty-hunter-toolkit
- https://github.com/AMEOBIUS-team/fastapi-template
- Portfolio: https://ameobius-team.github.io/kwork-portfolio/

Freelance portfolio: [https://ameobius-space.github.io/kwork-portfolio/](https://ameobius-space.github.io/kwork-portfolio/)
