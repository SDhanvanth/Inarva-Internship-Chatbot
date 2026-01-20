"""
Inbuilt MCP Server for the AI Platform.

Provides built-in AI tools powered by Google Gemini that are available
to all users without requiring external MCP server setup.
"""
import logging
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from app.mcp.gemini import gemini_client, get_gemini_client
from app.config import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/inbuilt-mcp", tags=["Inbuilt MCP Server"])


# ============================================================================
# Request/Response Models
# ============================================================================

class ToolParameter(BaseModel):
    """Schema for tool parameter definition."""
    type: str
    description: str
    required: bool = False
    enum: Optional[List[str]] = None
    default: Optional[Any] = None


class ToolDefinition(BaseModel):
    """Schema for tool definition in MCP format."""
    name: str
    description: str
    inputSchema: Dict[str, Any]


class ToolListRequest(BaseModel):
    """Request for listing tools."""
    pass


class ToolListResponse(BaseModel):
    """Response containing available tools."""
    tools: List[ToolDefinition]


class ToolCallRequest(BaseModel):
    """Request for invoking a tool."""
    name: str = Field(..., description="Name of the tool to invoke")
    arguments: Dict[str, Any] = Field(default_factory=dict, description="Tool arguments")


class ToolCallResponse(BaseModel):
    """Response from tool invocation."""
    content: Any
    isError: bool = False
    error: Optional[Dict[str, str]] = None


# ============================================================================
# Tool Definitions
# ============================================================================

INBUILT_TOOLS: List[ToolDefinition] = [
    ToolDefinition(
        name="chat",
        description="Have a conversation with the AI assistant. Ask questions, get help, or just chat.",
        inputSchema={
            "type": "object",
            "properties": {
                "message": {
                    "type": "string",
                    "description": "Your message to the AI assistant"
                },
                "system_prompt": {
                    "type": "string",
                    "description": "Optional system prompt to set context for the conversation"
                }
            },
            "required": ["message"]
        }
    ),
    ToolDefinition(
        name="summarize",
        description="Summarize text content into a concise form. Great for long articles, documents, or notes.",
        inputSchema={
            "type": "object",
            "properties": {
                "text": {
                    "type": "string",
                    "description": "The text content to summarize"
                },
                "max_length": {
                    "type": "integer",
                    "description": "Optional maximum length for the summary in words"
                }
            },
            "required": ["text"]
        }
    ),
    ToolDefinition(
        name="analyze",
        description="Analyze content and provide insights. Supports different analysis types like sentiment, key points extraction, and general analysis.",
        inputSchema={
            "type": "object",
            "properties": {
                "content": {
                    "type": "string",
                    "description": "The content to analyze"
                },
                "analysis_type": {
                    "type": "string",
                    "description": "Type of analysis to perform",
                    "enum": ["general", "sentiment", "key_points", "structured"],
                    "default": "general"
                }
            },
            "required": ["content"]
        }
    ),
    ToolDefinition(
        name="code_explain",
        description="Explain code snippets in plain language. Supports multiple programming languages and detail levels.",
        inputSchema={
            "type": "object",
            "properties": {
                "code": {
                    "type": "string",
                    "description": "The code snippet to explain"
                },
                "language": {
                    "type": "string",
                    "description": "Programming language of the code (optional, will auto-detect)"
                },
                "detail_level": {
                    "type": "string",
                    "description": "Level of detail for the explanation",
                    "enum": ["brief", "medium", "detailed"],
                    "default": "medium"
                }
            },
            "required": ["code"]
        }
    )
]


# ============================================================================
# MCP Server Endpoints
# ============================================================================

@router.get("/health")
async def health_check():
    """Health check endpoint for the inbuilt MCP server."""
    client = get_gemini_client()
    return {
        "status": "healthy",
        "service": "inbuilt-mcp-server",
        "gemini_configured": client.is_configured,
        "tools_available": len(INBUILT_TOOLS),
        "enabled": settings.INBUILT_MCP_ENABLED
    }


@router.post("/tools/list", response_model=ToolListResponse)
async def list_tools(request: ToolListRequest = None):
    """
    List available tools from the inbuilt MCP server.
    
    This follows the MCP protocol for tool discovery.
    """
    if not settings.INBUILT_MCP_ENABLED:
        return ToolListResponse(tools=[])
    
    return ToolListResponse(tools=INBUILT_TOOLS)


@router.post("/tools/call", response_model=ToolCallResponse)
async def call_tool(request: ToolCallRequest):
    """
    Invoke a tool from the inbuilt MCP server.
    
    This follows the MCP protocol for tool invocation.
    """
    if not settings.INBUILT_MCP_ENABLED:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Inbuilt MCP server is disabled"
        )
    
    client = get_gemini_client()
    
    if not client.is_configured:
        return ToolCallResponse(
            content=None,
            isError=True,
            error={
                "code": "gemini_not_configured",
                "message": "Gemini AI is not configured. Please set GEMINI_API_KEY environment variable."
            }
        )
    
    tool_name = request.name
    arguments = request.arguments
    
    # Route to appropriate tool handler
    if tool_name == "chat":
        result = await client.chat(
            message=arguments.get("message", ""),
            system_prompt=arguments.get("system_prompt")
        )
        if result["success"]:
            return ToolCallResponse(content={"response": result["response"], "model": result.get("model")})
        else:
            return ToolCallResponse(
                content=None,
                isError=True,
                error={"code": "chat_error", "message": result.get("error", "Unknown error")}
            )
    
    elif tool_name == "summarize":
        result = await client.summarize(
            text=arguments.get("text", ""),
            max_length=arguments.get("max_length")
        )
        if result["success"]:
            return ToolCallResponse(content={
                "summary": result["summary"],
                "original_length": result.get("original_length"),
                "model": result.get("model")
            })
        else:
            return ToolCallResponse(
                content=None,
                isError=True,
                error={"code": "summarize_error", "message": result.get("error", "Unknown error")}
            )
    
    elif tool_name == "analyze":
        result = await client.analyze(
            content=arguments.get("content", ""),
            analysis_type=arguments.get("analysis_type", "general")
        )
        if result["success"]:
            return ToolCallResponse(content={
                "analysis": result["analysis"],
                "analysis_type": result.get("analysis_type"),
                "model": result.get("model")
            })
        else:
            return ToolCallResponse(
                content=None,
                isError=True,
                error={"code": "analyze_error", "message": result.get("error", "Unknown error")}
            )
    
    elif tool_name == "code_explain":
        result = await client.explain_code(
            code=arguments.get("code", ""),
            language=arguments.get("language"),
            detail_level=arguments.get("detail_level", "medium")
        )
        if result["success"]:
            return ToolCallResponse(content={
                "explanation": result["explanation"],
                "language": result.get("language"),
                "detail_level": result.get("detail_level"),
                "model": result.get("model")
            })
        else:
            return ToolCallResponse(
                content=None,
                isError=True,
                error={"code": "code_explain_error", "message": result.get("error", "Unknown error")}
            )
    
    else:
        return ToolCallResponse(
            content=None,
            isError=True,
            error={
                "code": "unknown_tool",
                "message": f"Tool '{tool_name}' is not available. Available tools: {[t.name for t in INBUILT_TOOLS]}"
            }
        )


# ============================================================================
# Helper Functions
# ============================================================================

def get_inbuilt_mcp_endpoint() -> str:
    """Get the internal URL for the inbuilt MCP server."""
    return f"http://localhost:{settings.PORT}/inbuilt-mcp"


def get_inbuilt_tools_as_capabilities() -> Dict[str, Any]:
    """Get the inbuilt tools in the format used by capabilities field."""
    return {
        "tools": [
            {
                "name": tool.name,
                "description": tool.description,
                "parameters": tool.inputSchema,
                "app_id": "inbuilt-gemini-chatbot",
                "app_name": "Gemini AI Assistant"
            }
            for tool in INBUILT_TOOLS
        ]
    }
