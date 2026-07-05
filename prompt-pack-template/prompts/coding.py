"""Coding prompt pack — structured prompts for code generation, review, and debugging."""

CODING_PROMPTS = {
    "generate_function": {
        "name": "Generate Function",
        "category": "code_generation",
        "template": """Write a {language} function called `{function_name}` that {description}.

Requirements:
- Input: {input_type}
- Output: {output_type}
- Error handling: {error_handling}
- Include docstring with args, returns, raises
- Include type hints
- Include 3 test cases

Function signature: `{signature}`""",
        "variables": ["language", "function_name", "description", "input_type", "output_type", "error_handling", "signature"],
    },
    "code_review": {
        "name": "Code Review",
        "category": "review",
        "template": """Review the following {language} code for:
1. Security vulnerabilities (OWASP Top 10)
2. Performance bottlenecks
3. Code style violations ({style_guide})
4. Bug risks (null/undefined, race conditions, edge cases)
5. Documentation gaps

Code:
```{language}
{code}
```

Output format:
- Severity: CRITICAL/HIGH/MEDIUM/LOW
- Issue: description
- Location: line number
- Fix: suggested code""",
        "variables": ["language", "style_guide", "code"],
    },
    "debug_error": {
        "name": "Debug Error",
        "category": "debugging",
        "template": """Debug the following error in {language}:

Error message:
```
{error_message}
```

Stack trace:
```
{stack_trace}
```

Relevant code:
```{language}
{code}
```

Analyze:
1. Root cause
2. Why it happened
3. Fix (with code)
4. Prevention strategy""",
        "variables": ["language", "error_message", "stack_trace", "code"],
    },
    "refactor": {
        "name": "Refactor Code",
        "category": "refactoring",
        "template": """Refactor the following {language} code applying:
- SOLID principles
- DRY (Don't Repeat Yourself)
- Single Responsibility
- Extract method where needed
- Improve naming
- Add type hints if missing

Original:
```{language}
{code}
```

Output: refactored code + summary of changes""",
        "variables": ["language", "code"],
    },
    "test_generation": {
        "name": "Generate Tests",
        "category": "testing",
        "template": """Generate {test_framework} tests for the following {language} function:

```{language}
{code}
```

Include:
- Happy path tests (3 cases)
- Edge cases (empty, null, boundary)
- Error cases (invalid input, exceptions)
- Mock setup if needed
- Coverage target: 100%

Test framework: {test_framework}""",
        "variables": ["language", "test_framework", "code"],
    },
}


def get_prompt(name: str, **kwargs) -> str:
    """Get a formatted prompt by name."""
    if name not in CODING_PROMPTS:
        raise ValueError(f"Unknown prompt: {name}. Available: {list(CODING_PROMPTS.keys())}")
    p = CODING_PROMPTS[name]
    missing = [v for v in p["variables"] if v not in kwargs]
    if missing:
        raise ValueError(f"Missing variables for '{name}': {missing}")
    return p["template"].format(**kwargs)


def list_prompts() -> list:
    """List all available prompts."""
    return [
        {"name": p["name"], "category": p["category"], "variables": p["variables"]}
        for p in CODING_PROMPTS.values()
    ]
