# JSON-RPC Server: Lightweight RPC Without Frameworks

> Part of the [darkbot-templates](https://github.com/AMEOBIUS-space/darkbot-ai-templates) series — zero-dependency production templates.

REST is everywhere, but it's verbose for internal APIs. JSON-RPC 2.0 gives you typed method calls over HTTP — no URL paths, no status code hunting, just `{"method": "add", "params": [1, 2]}` → `{"result": 3}`.

## Usage

```python
from darkbot_templates.templates.jsonrpc_server import JSONRPCServer

rpc = JSONRPCServer()

@rpc.method("add")
def add(a, b):
    return a + b

@rpc.method("greet")
def greet(name, greeting="Hello"):
    return f"{greeting}, {name}!"

# Handle a request
request = {"jsonrpc": "2.0", "method": "add", "params": [3, 4], "id": 1}
response = rpc.handle(request)
# {"jsonrpc": "2.0", "result": 7, "id": 1}

# Named params
request = {"jsonrpc": "2.0", "method": "greet", "params": {"name": "World"}, "id": 2}
response = rpc.handle(request)
# {"jsonrpc": "2.0", "result": "Hello, World!", "id": 2}
```

## Standard Error Codes

```python
from darkbot_templates.templates.jsonrpc_server import JSONRPCError

@rpc.method("divide")
def divide(a, b):
    if b == 0:
        raise JSONRPCError(JSONRPCError.INVALID_PARAMS, "Division by zero")
    return a / b

# Client sees:
# {"jsonrpc": "2.0", "error": {"code": -32602, "message": "Division by zero"}, "id": 3}
```

| Code | Meaning |
|------|---------|
| -32700 | Parse error (invalid JSON) |
| -32600 | Invalid Request |
| -32601 | Method not found |
| -32602 | Invalid params |
| -32603 | Internal error |

## Batch Requests

Send multiple calls in one HTTP round-trip:

```python
batch = [
    {"jsonrpc": "2.0", "method": "add", "params": [1, 2], "id": 1},
    {"jsonrpc": "2.0", "method": "add", "params": [3, 4], "id": 2},
    {"jsonrpc": "2.0", "method": "greet", "params": {"name": "RPC"}, "id": 3},
]

responses = rpc.handle(batch)
# [
#   {"jsonrpc": "2.0", "result": 3, "id": 1},
#   {"jsonrpc": "2.0", "result": 7, "id": 2},
#   {"jsonrpc": "2.0", "result": "Hello, RPC!", "id": 3},
# ]
```

## Notifications (Fire-and-Forget)

Requests without an `id` are notifications — the server processes them but sends no response:

```python
# Client sends:
{"jsonrpc": "2.0", "method": "log", "params": {"level": "info", "msg": "started"}}

# Server processes, returns None (no response sent)
```

## Running as HTTP Server

```python
rpc = JSONRPCServer()

@rpc.method("ping")
def ping():
    return "pong"

# Start built-in HTTP server on port 9000
rpc.serve(host="0.0.0.0", port=9000)

# Test:
# curl -X POST http://localhost:9000 -d '{"jsonrpc":"2.0","method":"ping","id":1}'
# → {"jsonrpc": "2.0", "result": "pong", "id": 1}
```

## MCP Protocol Foundation

JSON-RPC 2.0 is the transport for MCP (Model Context Protocol). This server template is the foundation for building custom MCP servers:

```python
rpc = JSONRPCServer()

@rpc.method("tools/list")
def list_tools():
    return {"tools": [{"name": "search", "description": "Search the web"}]}

@rpc.method("tools/call")
def call_tool(name, arguments):
    if name == "search":
        return search(arguments["query"])
```

## Testing

```bash
pytest tests/test_jsonrpc_cli.py -v
```

## References

- [JSON-RPC 2.0 Spec](https://www.jsonrpc.org/specification)
- [MCP Protocol](https://modelcontextprotocol.io/) — uses JSON-RPC 2.0

---

*darkbot-templates v1.8.5 — 30 templates, zero dependencies, 448 tests.*
