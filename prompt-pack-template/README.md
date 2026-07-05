# AI Prompt Pack Template

> 5 structured coding prompts for AI-assisted development

## Prompts

1. **Generate Function** — code generation with type hints + tests
2. **Code Review** — security, performance, style, bugs, docs
3. **Debug Error** — root cause analysis with stack trace
4. **Refactor Code** — SOLID, DRY, naming, type hints
5. **Generate Tests** — happy path + edge cases + error cases

## Quick Start

```python
from coding import get_prompt

prompt = get_prompt("code_review", language="python", style_guide="PEP 8", code="...")
print(prompt)
```

## Tests

```bash
python -m pytest tests/ -v
```

## License

MIT
