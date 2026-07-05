# JSON-RPC Server

> JSON-RPC 2.0 protocol with method registration, batch support, and middleware

## Features

- JSON-RPC 2.0 spec compliant
- Method registration (single + module)
- Positional and named parameters
- Batch request support
- Notifications (no response)
- Standard error codes (-32700, -32600, -32601, -32602, -32603)
- Middleware support
- Direct method calling (bypass JSON)
- Method listing and existence check

## Quick Start

```python
from rpc import JSONRPCServer

server = JSONRPCServer()
server.register("add", lambda a, b: a + b)
server.register("greet", lambda name: f"Hello, {name}!")

# Handle request
response = server.handle('{"jsonrpc": "2.0", "method": "add", "params": [2, 3], "id": 1}')
# => {"jsonrpc": "2.0", "result": 5, "id": 1}
```

## Tests

```bash
python -m pytest tests/ -v
```

## License

MIT
