"""MCP package initialization."""

from app.mcp.client import MCPClient, mcp_client, get_mcp_client, Tool, ToolResult
from app.mcp.gemini import GeminiClient, gemini_client, get_gemini_client
from app.mcp.server import router as inbuilt_mcp_router, INBUILT_TOOLS

__all__ = [
    "MCPClient", "mcp_client", "get_mcp_client", "Tool", "ToolResult",
    "GeminiClient", "gemini_client", "get_gemini_client",
    "inbuilt_mcp_router", "INBUILT_TOOLS"
]
