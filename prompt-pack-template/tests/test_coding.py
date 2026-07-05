import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "prompts"))
from coding import get_prompt, list_prompts, CODING_PROMPTS


def test_list_prompts():
    prompts = list_prompts()
    assert len(prompts) == 5
    categories = [p["category"] for p in prompts]
    assert "code_generation" in categories
    assert "review" in categories
    assert "debugging" in categories


def test_get_prompt_generate():
    result = get_prompt(
        "generate_function",
        language="python",
        function_name="calc",
        description="does math",
        input_type="int",
        output_type="int",
        error_handling="raise ValueError",
        signature="def calc(x: int) -> int",
    )
    assert "python" in result
    assert "calc" in result


def test_get_prompt_review():
    result = get_prompt(
        "code_review",
        language="python",
        style_guide="PEP 8",
        code="print('hello')",
    )
    assert "Security" in result
    assert "PEP 8" in result


def test_get_prompt_debug():
    result = get_prompt(
        "debug_error",
        language="python",
        error_message="TypeError",
        stack_trace="line 10",
        code="x = 1 + 'a'",
    )
    assert "TypeError" in result
    assert "Root cause" in result


def test_get_prompt_test_gen():
    result = get_prompt(
        "test_generation",
        language="python",
        test_framework="pytest",
        code="def add(a, b): return a + b",
    )
    assert "pytest" in result
    assert "100%" in result


def test_unknown_prompt():
    try:
        get_prompt("nonexistent")
        assert False, "Should have raised"
    except ValueError as e:
        assert "Unknown prompt" in str(e)


def test_missing_variables():
    try:
        get_prompt("generate_function", language="python")
        assert False, "Should have raised"
    except ValueError as e:
        assert "Missing variables" in str(e)
