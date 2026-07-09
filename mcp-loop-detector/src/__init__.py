"""mcp-loop-detector package — MCP server for agent loop detection."""
from .loop_detector_engine import LoopDetector
from .server import MCPLoopDetectorServer, TOOL_DEFS
__all__ = ["LoopDetector", "MCPLoopDetectorServer", "TOOL_DEFS"]
__version__ = "1.0.0"
