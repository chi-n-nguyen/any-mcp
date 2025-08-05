"""
Core types for the Universal MCP Adapter.
"""

from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field
from enum import Enum


class MCPTransportType(str, Enum):
    """Supported MCP transport types."""
    STDIO = "stdio"
    HTTP = "http"
    WEBSOCKET = "websocket"


class MCPToolSpec(BaseModel):
    """Specification for an MCP tool."""
    name: str = Field(..., description="Tool name")
    description: str = Field(..., description="Tool description")
    input_schema: Dict[str, Any] = Field(..., description="JSON schema for input")
    output_schema: Optional[Dict[str, Any]] = Field(None, description="JSON schema for output")


class MCPRequest(BaseModel):
    """MCP request structure."""
    jsonrpc: str = "2.0"
    id: Union[str, int]
    method: str
    params: Optional[Dict[str, Any]] = None


class MCPResponse(BaseModel):
    """MCP response structure."""
    jsonrpc: str = "2.0"
    id: Union[str, int]
    result: Optional[Any] = None
    error: Optional[Dict[str, Any]] = None


class MCPError(Exception):
    """MCP-specific error."""
    def __init__(self, code: int, message: str, data: Optional[Any] = None):
        self.code = code
        self.message = message
        self.data = data
        super().__init__(f"MCP Error {code}: {message}")


class MCPConfig(BaseModel):
    """Configuration for an MCP instance."""
    name: str
    transport: MCPTransportType
    command: Optional[str] = None
    args: Optional[List[str]] = None
    url: Optional[str] = None
    timeout: int = 30
    max_memory_mb: int = 512
    health_check_interval: int = 30 