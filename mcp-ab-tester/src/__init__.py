"""mcp-ab-tester package — MCP server for A/B testing."""
from .ab_tester_engine import ABTester
from .server import MCPABTesterServer, TOOL_DEFS
__all__ = ["ABTester", "MCPABTesterServer", "TOOL_DEFS"]
__version__ = "1.0.0"
