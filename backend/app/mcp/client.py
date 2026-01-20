"""
MCP (Model Context Protocol) client for tool invocation.
"""
import asyncio
import hashlib
import hmac
import json
import logging
import time
from typing import Optional, Any, List, Dict
from dataclasses import dataclass
import httpx

from app.config import settings
from app.core.security import decrypt_value

logger = logging.getLogger(__name__)


@dataclass
class Tool:
    """Represents an MCP tool."""
    name: str
    description: str
    parameters: Dict[str, Any]
    app_id: str
    app_name: str


@dataclass
class ToolResult:
    """Result from tool invocation."""
    success: bool
    result: Any
    error: Optional[str] = None
    duration_ms: int = 0


class MCPClient:
    """
    MCP Client for communicating with MCP servers.
    
    Handles:
    - Tool discovery
    - Tool invocation with retries
    - Request signing
    - Response validation
    """
    
    def __init__(self):
        self.http_client = httpx.AsyncClient(
            timeout=httpx.Timeout(settings.MCP_DEFAULT_TIMEOUT),
            follow_redirects=True
        )
    
    async def close(self):
        """Close HTTP client."""
        await self.http_client.aclose()
    
    def _sign_request(
        self,
        endpoint: str,
        method: str,
        body: str,
        api_key: str
    ) -> Dict[str, str]:
        """Sign request for MCP server authentication."""
        timestamp = str(int(time.time()))
        message = f"{method}\n{endpoint}\n{timestamp}\n{body}"
        signature = hmac.new(
            api_key.encode(),
            message.encode(),
            hashlib.sha256
        ).hexdigest()
        
        return {
            "X-MCP-Timestamp": timestamp,
            "X-MCP-Signature": signature,
        }
    
    async def discover_tools(
        self,
        mcp_endpoint: str,
        api_key_encrypted: Optional[str] = None,
        app_id: str = "",
        app_name: str = ""
    ) -> List[Tool]:
        """
        Discover available tools from MCP server.
        
        Calls the /tools/list endpoint on the MCP server.
        """
        try:
            headers = {"Content-Type": "application/json"}
            
            # Add authentication if API key provided
            if api_key_encrypted:
                api_key = decrypt_value(api_key_encrypted)
                headers["Authorization"] = f"Bearer {api_key}"
            
            response = await self.http_client.post(
                f"{mcp_endpoint.rstrip('/')}/tools/list",
                headers=headers,
                json={}
            )
            response.raise_for_status()
            
            data = response.json()
            tools = []
            
            for tool_data in data.get("tools", []):
                tools.append(Tool(
                    name=tool_data.get("name", ""),
                    description=tool_data.get("description", ""),
                    parameters=tool_data.get("inputSchema", {}),
                    app_id=app_id,
                    app_name=app_name
                ))
            
            logger.info(f"Discovered {len(tools)} tools from {mcp_endpoint}")
            return tools
            
        except httpx.HTTPError as e:
            logger.error(f"HTTP error discovering tools from {mcp_endpoint}: {e}")
            return []
        except Exception as e:
            logger.error(f"Error discovering tools from {mcp_endpoint}: {e}")
            return []
    
    async def invoke_tool(
        self,
        mcp_endpoint: str,
        tool_name: str,
        arguments: Dict[str, Any],
        api_key_encrypted: Optional[str] = None
    ) -> ToolResult:
        """
        Invoke a tool on the MCP server.
        
        Implements retry logic and timeout handling.
        """
        start_time = time.time()
        
        for attempt in range(settings.MCP_MAX_RETRIES):
            try:
                headers = {"Content-Type": "application/json"}
                
                # Add authentication if API key provided
                if api_key_encrypted:
                    api_key = decrypt_value(api_key_encrypted)
                    headers["Authorization"] = f"Bearer {api_key}"
                    
                    # Sign request
                    body = json.dumps({
                        "name": tool_name,
                        "arguments": arguments
                    })
                    signing_headers = self._sign_request(
                        mcp_endpoint,
                        "POST",
                        body,
                        api_key
                    )
                    headers.update(signing_headers)
                
                response = await self.http_client.post(
                    f"{mcp_endpoint.rstrip('/')}/tools/call",
                    headers=headers,
                    json={
                        "name": tool_name,
                        "arguments": arguments
                    }
                )
                response.raise_for_status()
                
                data = response.json()
                duration_ms = int((time.time() - start_time) * 1000)
                
                # Check for error in response
                if "error" in data:
                    return ToolResult(
                        success=False,
                        result=None,
                        error=data["error"].get("message", "Unknown error"),
                        duration_ms=duration_ms
                    )
                
                return ToolResult(
                    success=True,
                    result=data.get("content", data.get("result")),
                    duration_ms=duration_ms
                )
                
            except httpx.TimeoutException:
                if attempt < settings.MCP_MAX_RETRIES - 1:
                    await asyncio.sleep(settings.MCP_RETRY_DELAY * (attempt + 1))
                    continue
                    
                duration_ms = int((time.time() - start_time) * 1000)
                return ToolResult(
                    success=False,
                    result=None,
                    error="Request timed out",
                    duration_ms=duration_ms
                )
                
            except httpx.HTTPStatusError as e:
                duration_ms = int((time.time() - start_time) * 1000)
                return ToolResult(
                    success=False,
                    result=None,
                    error=f"HTTP {e.response.status_code}: {e.response.text[:200]}",
                    duration_ms=duration_ms
                )
                
            except Exception as e:
                duration_ms = int((time.time() - start_time) * 1000)
                return ToolResult(
                    success=False,
                    result=None,
                    error=str(e),
                    duration_ms=duration_ms
                )
        
        duration_ms = int((time.time() - start_time) * 1000)
        return ToolResult(
            success=False,
            result=None,
            error="Max retries exceeded",
            duration_ms=duration_ms
        )
    
    async def validate_endpoint(self, mcp_endpoint: str) -> bool:
        """Validate that an MCP endpoint is reachable."""
        try:
            response = await self.http_client.get(
                f"{mcp_endpoint.rstrip('/')}/health",
                timeout=5.0
            )
            return response.status_code < 500
        except Exception:
            return False


# Global MCP client instance
mcp_client = MCPClient()


async def get_mcp_client() -> MCPClient:
    """Dependency to get MCP client."""
    return mcp_client
