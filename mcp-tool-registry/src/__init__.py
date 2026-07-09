"""mcp-tool-registry package — MCP server for dynamic tool management."""
from .tool_registry_engine import ToolRegistry
from .server import MCPToolRegistryServer, TOOL_DEFS
__all__ = ["ToolRegistry", "MCPToolRegistryServer", "TOOL_DEFS"]
__version__ = "1.0.0"
