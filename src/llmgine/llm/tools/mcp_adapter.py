"""
MCP Tool Adapter for LLMgine

Converts MCP tools to LLMgine format and handles execution.
"""

import json
import logging
from typing import Any, Dict

from mcp.types import Tool, CallToolResult
from .mcp_client import SimpleMCPClient

logger = logging.getLogger(__name__)


class MCPToolAdapter:
    """Adapter that converts MCP tools to work with LLMgine's ToolManager."""
    
    def __init__(self, mcp_client: SimpleMCPClient):
        self.mcp_client = mcp_client
    
    def convert_mcp_tool_to_schema(self, mcp_tool: Tool) -> Dict[str, Any]:
        """Convert MCP tool to OpenAI-format schema for LLMgine."""
        # MCP tools already have JSON schema format, just adapt to OpenAI format
        return {
            "type": "function",
            "function": {
                "name": mcp_tool.name,
                "description": mcp_tool.description or f"MCP tool: {mcp_tool.name}",
                "parameters": mcp_tool.inputSchema or {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            }
        }
    
    def create_mcp_tool_function(self, tool_name: str):
        """Create a function that calls the MCP tool."""
        async def mcp_tool_wrapper(**kwargs) -> str:
            """Wrapper function that calls MCP tool and returns string result."""
            try:
                # Call the MCP tool
                result = await self.mcp_client.call_tool(tool_name, kwargs)
                
                # Convert result to string
                return self._convert_result_to_string(result)
                
            except Exception as e:
                logger.error(f"Error calling MCP tool {tool_name}: {e}")
                return f"Error: {str(e)}"
        
        # Set function name for registration
        mcp_tool_wrapper.__name__ = tool_name
        mcp_tool_wrapper.__doc__ = f"MCP tool: {tool_name}"
        
        return mcp_tool_wrapper
    
    def _convert_result_to_string(self, result: CallToolResult) -> str:
        """Convert MCP CallToolResult to string for LLMgine."""
        if not result:
            return "No result"
        
        # Handle error results
        if getattr(result, 'isError', False):
            return f"Error: {self._extract_text_content(result)}"
        
        # Extract text content
        return self._extract_text_content(result)
    
    def _extract_text_content(self, result: CallToolResult) -> str:
        """Extract text content from MCP result."""
        try:
            if hasattr(result, 'content') and result.content:
                # Try to get text from content items
                text_parts = []
                for item in result.content:
                    if hasattr(item, 'text') and item.text:
                        text_parts.append(item.text)
                
                if text_parts:
                    return " ".join(text_parts)
            
            # Fallback to string representation
            return str(result)
            
        except Exception as e:
            logger.error(f"Error extracting text from MCP result: {e}")
            return str(result)