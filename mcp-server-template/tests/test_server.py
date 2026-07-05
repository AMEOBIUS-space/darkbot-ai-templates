import asyncio
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from server import create_example_server, MCPServer, Tool, Resource, Prompt


def test_manifest():
    server = create_example_server()
    m = server.manifest()
    assert m["server"]["name"] == "example-mcp-server"
    assert len(m["tools"]) == 3
    assert len(m["resources"]) == 1
    assert len(m["prompts"]) == 1


def test_list_tools():
    server = create_example_server()
    tools = server.list_tools()
    names = [t["name"] for t in tools]
    assert "echo" in names
    assert "calculate" in names
    assert "timestamp" in names


def test_echo_tool():
    server = create_example_server()
    result = asyncio.run(server.handle_tool_call("echo", {"text": "hello"}))
    assert "hello" in result


def test_calculate_tool():
    server = create_example_server()
    result = asyncio.run(server.handle_tool_call("calculate", {"expression": "2+2"}))
    assert "4" in result


def test_timestamp_tool():
    server = create_example_server()
    result = asyncio.run(server.handle_tool_call("timestamp", {}))
    assert len(result) > 0


def test_unknown_tool():
    server = create_example_server()
    result = asyncio.run(server.handle_tool_call("nonexistent", {}))
    assert "not found" in result


def test_custom_tool():
    server = MCPServer("custom")
    server.register_tool(Tool(
        name="custom",
        description="Custom tool",
        input_schema={"type": "object", "properties": {}},
        handler=lambda: "custom result",
    ))
    result = asyncio.run(server.handle_tool_call("custom", {}))
    assert "custom result" in result
