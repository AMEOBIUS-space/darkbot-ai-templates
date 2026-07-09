# Contributing to DarkBot AI Templates

Thank you for your interest in contributing! This project is a collection of 168 production-ready Python templates with zero external dependencies.

## How to Contribute

### Report Bugs

1. Check existing issues to avoid duplicates
2. Open a new issue with:
   - Template name (e.g., `mcp-context-guard`)
   - Python version
   - Steps to reproduce
   - Expected vs actual behavior

### Suggest New Templates

1. Open an issue with the `template-request` label
2. Describe the use case and target audience
3. Explain why zero-dependency matters for this template

### Submit a Pull Request

1. Fork the repository
2. Create a branch: `git checkout -b feature/my-template`
3. Add your template under the appropriate directory
4. Include:
   - `src/` — source code (pure Python stdlib, no pip dependencies)
   - `tests/` — pytest test suite
   - `README.md` — with install instructions and examples
   - `LICENSE` — MIT
   - `Makefile` — `make test` target
5. Run tests: `python -m pytest tests/ -v`
6. Commit: `git commit -m "feat: add my-template"`
7. Push: `git push origin feature/my-template`
8. Open a PR

### Code Standards

- **Zero dependencies**: Only Python standard library
- **Python 3.10+**: Use modern syntax (match statements, type hints)
- **Test coverage**: 80%+ for new templates
- **Documentation**: Every public function has a docstring
- **Naming**: snake_case for files and functions, PascalCase for classes

### Commit Message Format

```
type: short description

type can be: feat, fix, docs, test, refactor, chore
```

Examples:
- `feat: add mcp-token-budget server`
- `fix: resolve NoneType error in hash_text`
- `docs: improve README for cdp-toolkit`
- `test: add edge cases for permission guard`

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
