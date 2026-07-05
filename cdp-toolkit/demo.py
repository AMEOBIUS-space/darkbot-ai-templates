#!/usr/bin/env python3
"""Demo: CDP Toolkit — browser automation helpers."""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))
from cdp_client import CDPClient, CDPMouseEvents, CDPInput, CDPNavigation


def main():
    print("=== CDP Toolkit Demo ===\n")

    # Mouse events
    print("Mouse click at (741, 496):")
    print(f"  {CDPMouseEvents.click_params(741, 496)}")
    print(f"  {CDPMouseEvents.release_params(741, 496)}")

    # Input
    print("\nInsert text 'hello':")
    print(f"  {CDPInput.insert_text_params('hello')}")

    # Native setter for React forms
    print("\nReact native setter JS:")
    js = CDPInput.native_setter_js("#email", "test@example.com")
    print(f"  {js[:100]}...")

    # Navigation
    print("\nNavigate to https://example.com:")
    print(f"  {CDPNavigation.navigate_params('https://example.com')}")

    # Screenshot
    print("\nScreenshot params:")
    print(f"  {CDPNavigation.screenshot_params('png', 90)}")

    # Evaluate JS
    print("\nEvaluate JS:")
    print(f"  {CDPNavigation.evaluate_params('document.title')}")

    # CDPClient (won't connect in demo, but shows API)
    print("\nCDPClient API:")
    client = CDPClient("127.0.0.1", 9222)
    print(f"  host={client.host} port={client.port}")
    print(f"  Methods: list_targets, create_target, close_target, activate_target, get_version")


if __name__ == "__main__":
    main()
