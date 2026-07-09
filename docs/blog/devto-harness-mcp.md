---
title: "10 Zero-Dependency MCP Servers Every AI Agent Harness Needs"
published: false
description: "132 tools. 289 tests. Zero pip dependencies. Pure Python stdlib MCP servers for context management, permissions, tracing, evaluation, and more."
tags: mcp, aiagents, python, opensource
cover_image: https://github.com/aaameobius-crypto/harness-engineering-suite/raw/main/assets/banner.svg
---

If you're building an AI agent harness, you need MCP servers for context management, permission checking, tracing, and evaluation. The problem? Most MCP servers pull in dozens of npm packages or pip dependencies, creating supply chain risk and breaking in sandboxed environments.

I built 10 MCP servers that solve this. **132 tools, 289 tests, zero external dependencies.** Just Python 3.8+ standard library.

## The Servers

| Server | Tools | Tests | Purpose |
|--------|-------|-------|---------|
| [context-guard](https://github.com/aaameobius-crypto/mcp-context-guard) | 14 | 36 | Compress, deduplicate, filter tool outputs |
| [permission-guard](https://github.com/aaameobius-crypto/mcp-permission-guard) | 12 | 38 | Intent-based authorization with risk scoring |
| [agent-trace](https://github.com/aaameobius-crypto/mcp-agent-trace) | 14 | 28 | Trace trees, metrics, loop detection |
| [eval-harness](https://github.com/aaameobius-crypto/mcp-eval-harness) | 12 | 34 | Behavior benchmarks, regression testing |
| [skill-router](https://github.com/aaameobius-crypto/mcp-skill-router) | 12 | 27 | Intent-based skill routing |
| [prompt-versioning](https://github.com/aaameobius-crypto/mcp-prompt-versioning) | 15 | 28 | Prompt version control with diff/rollback |
| [token-budget](https://github.com/aaameobius-crypto/mcp-token-budget) | 12 | 25 | Token cost tracking, budget alerts |
| [loop-detector](https://github.com/aaameobius-crypto/mcp-loop-detector) | 10 | 24 | Repetition loop detection |
| [ab-tester](https://github.com/aaameobius-crypto/mcp-ab-tester) | 11 | 22 | A/B testing framework |
| [tool-registry](https://github.com/aaameobius-crypto/mcp-tool-registry) | 20 | 27 | Tool lifecycle management |

## Why Zero Dependencies?

Three reasons:

**1. Supply chain security.** The npm and PyPI ecosystems have been compromised multiple times. Every dependency is attack surface. Python's standard library is audited, stable, and ships with the interpreter.

**2. Sandboxed environments.** CI pipelines, Docker containers, and air-gapped systems don't always have network access. If your MCP server needs `pip install fastapi`, it's dead on arrival in those environments.

**3. Reproducibility.** No dependency version conflicts. No broken installs. The server that works on your machine works everywhere Python 3.8+ runs.

## How to Use Them

```bash
# Clone any server — no install step needed
git clone https://github.com/aaameobius-crypto/mcp-context-guard.git
cd mcp-context-guard

# Run tests (pytest works, but unittest discover also works)
python -m pytest tests/ -v

# Start the MCP server
python src/server.py
```

Add to Claude Desktop:
```json
{
  "mcpServers": {
    "context-guard": {
      "command": "python",
      "args": ["/path/to/mcp-context-guard/src/server.py"]
    }
  }
}
```

## Harness Coverage

The 10 servers map to the major layers of an agent harness:

```
┌─────────────────────────────────────────────┐
│              AGENT HARNESS LAYER            │
├──────────┬──────────┬───────────────────────┤
│ Context  │ Perms    │ Observability         │
│ context- │ permission│ agent-trace          │
│ guard    │ -guard   │ loop-detector         │
│ token-   │          │                       │
│ budget   │          │                       │
├──────────┼──────────┼───────────────────────┤
│ Verification & CI    │ Tooling              │
│ eval-harness         │ tool-registry        │
│ skill-router         │                      │
│ prompt-versioning    │                      │
│ ab-tester            │                      │
└──────────────────────┴──────────────────────┘
```

## The Zero-Dependency Design Pattern

Every server follows the same architecture:

1. **Transport:** JSON-RPC 2.0 over stdio (just `sys.stdin`/`sys.stdout`)
2. **Storage:** `sqlite3` module for persistence (traces, audit logs, test results)
3. **HTTP:** `urllib.request` for outbound calls
4. **Serialization:** `json` module
5. **Testing:** `unittest` (runs with or without pytest)

```python
import sys, json

def handle_request(request):
    method = request.get("method", "")
    if method == "tools/list":
        return {"tools": get_tool_definitions()}
    elif method == "tools/call":
        return execute_tool(request["params"]["name"], request["params"].get("arguments", {}))
    return {"error": {"code": -32601, "message": "Method not found"}}

for line in sys.stdin:
    req = json.loads(line)
    resp = handle_request(req)
    resp["jsonrpc"] = "2.0"
    resp["id"] = req.get("id")
    print(json.dumps(resp))
    sys.stdout.flush()
```

That's a working MCP server in 12 lines of pure Python.

## Links

- **Full suite:** [harness-engineering-suite](https://github.com/aaameobius-crypto/harness-engineering-suite)
- **GitHub profile:** [aaameobius-crypto](https://github.com/aaameobius-crypto)
- **Blog:** [DarkBot AI](https://github.com/aaameobius-crypto/darkbot-ai-templates/tree/main/docs)

---

*All servers are MIT licensed. No dependencies. No telemetry. No tracking. Just Python.*
