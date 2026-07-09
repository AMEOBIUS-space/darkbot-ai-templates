"""mcp-skill-router package — MCP server for intent-based skill routing."""
from .skill_router_engine import SkillRouter
from .server import MCPSkillRouterServer, TOOL_DEFS
__all__ = ["SkillRouter", "MCPSkillRouterServer", "TOOL_DEFS"]
__version__ = "1.0.0"
