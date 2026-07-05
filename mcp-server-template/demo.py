#!/usr/bin/env python3
"""Demo: MCP Server Template — run and test tools."""
import asyncio
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))
from server import create_example_server


async def main():
    server = create_example_server()
    import json
    print(json.dumps(server.manifest(), indent=2))
    print("\n=== Tool Calls ===")
    result = await server.handle_tool_call("echo", {"text": "Hello MCP!"})
    print(f"echo: {result}")
    result = await server.handle_tool_call("calculate", {"expression": "2 + 3 * 4"})
    print(f"calculate: {result}")
    result = await server.handle_tool_call("timestamp", {"format": "%Y-%m-%d"})
    print(f"timestamp: {result}")

if __name__ == "__main__":
    asyncio.run(main())
