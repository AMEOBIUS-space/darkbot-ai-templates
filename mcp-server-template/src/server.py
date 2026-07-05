"""MCP Server Template — Model Context Protocol server with tools, resources, and prompts."""
import json
import asyncio
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, asdict
from datetime import datetime


@dataclass
class Tool:
    name: str
    description: str
    input_schema: Dict[str, Any]
    handler: callable


@dataclass
class Resource:
    uri: str
    name: str
    description: str
    mime_type: str = "text/plain"


@dataclass
class Prompt:
    name: str
    description: str
    template: str


class MCPServer:
    """Minimal MCP server with tool/resource/prompt registration."""

    def __init__(self, name: str, version: str = "1.0.0"):
        self.name = name
        self.version = version
        self.tools: Dict[str, Tool] = {}
        self.resources: Dict[str, Resource] = {}
        self.prompts: Dict[str, Prompt] = {}

    def register_tool(self, tool: Tool):
        self.tools[tool.name] = tool

    def register_resource(self, resource: Resource):
        self.resources[resource.uri] = resource

    def register_prompt(self, prompt: Prompt):
        self.prompts[prompt.name] = prompt

    async def handle_tool_call(self, name: str, args: Dict[str, Any]) -> str:
        if name not in self.tools:
            return json.dumps({"error": f"Tool '{name}' not found"})
        try:
            result = self.tools[name].handler(**args)
            return json.dumps({"result": result}) if not isinstance(result, str) else result
        except Exception as e:
            return json.dumps({"error": str(e)})

    def list_tools(self) -> List[Dict]:
        return [
            {"name": t.name, "description": t.description, "inputSchema": t.input_schema}
            for t in self.tools.values()
        ]

    def list_resources(self) -> List[Dict]:
        return [asdict(r) for r in self.resources.values()]

    def list_prompts(self) -> List[Dict]:
        return [
            {"name": p.name, "description": p.description, "template": p.template}
            for p in self.prompts.values()
        ]

    def manifest(self) -> Dict:
        return {
            "server": {"name": self.name, "version": self.version},
            "capabilities": {"tools": {"listChanged": True}, "resources": {}, "prompts": {}},
            "tools": self.list_tools(),
            "resources": self.list_resources(),
            "prompts": self.list_prompts(),
        }


# Example tools
def echo(text: str) -> str:
    return f"Echo: {text}"


def calculate(expression: str) -> str:
    try:
        allowed = set("0123456789+-*/.() ")
        if all(c in allowed for c in expression):
            return str(eval(expression))
        return "Error: Invalid characters"
    except Exception as e:
        return f"Error: {e}"


def timestamp(format: str = "%Y-%m-%d %H:%M:%S") -> str:
    return datetime.now().strftime(format)


def create_example_server() -> MCPServer:
    server = MCPServer("example-mcp-server", "1.0.0")
    server.register_tool(Tool(
        name="echo",
        description="Echo back the input text",
        input_schema={"type": "object", "properties": {"text": {"type": "string"}}, "required": ["text"]},
        handler=echo,
    ))
    server.register_tool(Tool(
        name="calculate",
        description="Evaluate a math expression",
        input_schema={"type": "object", "properties": {"expression": {"type": "string"}}, "required": ["expression"]},
        handler=calculate,
    ))
    server.register_tool(Tool(
        name="timestamp",
        description="Get current timestamp",
        input_schema={"type": "object", "properties": {"format": {"type": "string"}}, "required": []},
        handler=timestamp,
    ))
    server.register_resource(Resource(
        uri="server://info",
        name="Server Info",
        description="Server metadata and version",
    ))
    server.register_prompt(Prompt(
        name="greet",
        description="Greeting prompt",
        template="Hello, {{name}}! Welcome to {{server}}.",
    ))
    return server


if __name__ == "__main__":
    server = create_example_server()
    print(json.dumps(server.manifest(), indent=2))
