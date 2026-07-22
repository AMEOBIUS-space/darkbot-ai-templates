# MCP Server Template

> Production-ready Model Context Protocol server with tools, resources, and prompts

## Features

- Tool registration with input schemas
- Resource management with URIs
- Prompt templates with variables
- JSON manifest output (MCP-compatible)
- Async tool call handling
- 3 example tools (echo, calculate, timestamp)

## Quick Start

```bash
python src/server.py
```

## Demo

```bash
python demo.py
```

## Tests

```bash
python -m pytest tests/ -v
```

## Add Your Own Tool

```python
from server import MCPServer, Tool

server = MCPServer("my-server")

server.register_tool(Tool(
    name="my_tool",
    description="Does something cool",
    input_schema={"type": "object", "properties": {"input": {"type": "string"}}, "required": ["input"]},
    handler=lambda input: f"Result: {input}",
))
```

## License

MIT

Freelance portfolio: [https://ameobius-space.github.io/kwork-portfolio/](https://ameobius-space.github.io/kwork-portfolio/)
