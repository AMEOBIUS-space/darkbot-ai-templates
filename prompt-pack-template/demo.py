#!/usr/bin/env python3
"""Demo: AI Prompt Pack — coding prompts for generation, review, debugging."""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "prompts"))
from coding import get_prompt, list_prompts


def main():
    print("=== Available Prompts ===")
    for p in list_prompts():
        print(f"  {p['name']} ({p['category']}): vars={p['variables']}")

    print("\n=== Generate Function Prompt ===")
    result = get_prompt(
        "generate_function",
        language="python",
        function_name="calculate_tax",
        description="calculates income tax based on brackets",
        input_type="float (annual income)",
        output_type="float (tax amount)",
        error_handling="raise ValueError for negative income",
        signature="def calculate_tax(income: float) -> float",
    )
    print(result[:200] + "...")

    print("\n=== Code Review Prompt ===")
    result = get_prompt(
        "code_review",
        language="python",
        style_guide="PEP 8",
        code="def add(a, b): return a + b",
    )
    print(result[:200] + "...")

    print("\n=== Debug Error Prompt ===")
    result = get_prompt(
        "debug_error",
        language="python",
        error_message="TypeError: unsupported operand type(s)",
        stack_trace="File 'app.py', line 10",
        code="result = 'hello' + 5",
    )
    print(result[:200] + "...")

    print("\n=== Test Generation Prompt ===")
    result = get_prompt(
        "test_generation",
        language="python",
        test_framework="pytest",
        code="def add(a, b): return a + b",
    )
    print(result[:200] + "...")


if __name__ == "__main__":
    main()
