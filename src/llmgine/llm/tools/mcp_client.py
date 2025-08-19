"""
Simple MCP Client for LLMgine Integration

Handles subprocess spawning and basic MCP communication.
"""

import asyncio
import logging
from contextlib import AsyncExitStack
from typing import Any, Dict, List, Optional

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from mcp.types import CallToolResult, Tool

logger = logging.getLogger(__name__)


class SimpleMCPClient:
    """Simple MCP client that spawns subprocess and handles basic communication."""
    
    def __init__(self, server_name: str):
        self.server_name = server_name
        self.session: Optional[ClientSession] = None
        self.exit_stack = AsyncExitStack()
        self._connected = False
        self._tools: List[Tool] = []
        
    async def start(self, command: str, args: List[str], env: Optional[Dict[str, str]] = None) -> bool:
        """Start MCP server subprocess and connect."""
        try:
            logger.info(f"Starting MCP server: {self.server_name}")
            
            # Create server parameters
            server_params = StdioServerParameters(
                command=command,
                args=args,
                env=env or {}
            )
            
            # Connect to server
            stdio_transport = await self.exit_stack.enter_async_context(
                stdio_client(server_params)
            )
            stdio, write = stdio_transport
            
            # Create session
            self.session = await self.exit_stack.enter_async_context(
                ClientSession(stdio, write)
            )
            
            # Initialize session
            await self.session.initialize()
            
            # Load tools
            response = await self.session.list_tools()
            self._tools = response.tools
            
            self._connected = True
            logger.info(f"MCP server {self.server_name} started with {len(self._tools)} tools")
            return True
            
        except Exception as e:
            logger.error(f"Failed to start MCP server {self.server_name}: {e}")
            self._connected = False
            return False
    
    def get_tools(self) -> List[Tool]:
        """Get available tools."""
        return self._tools
    
    async def call_tool(self, name: str, arguments: Dict[str, Any]) -> Optional[CallToolResult]:
        """Call a tool on the MCP server."""
        if not self._connected or not self.session:
            raise RuntimeError(f"MCP server {self.server_name} not connected")
        
        try:
            logger.debug(f"Calling MCP tool {name} with args: {arguments}")
            result = await self.session.call_tool(name, arguments)
            return result
        except Exception as e:
            logger.error(f"Error calling MCP tool {name}: {e}")
            raise
    
    async def stop(self):
        """Stop the MCP server and cleanup."""
        if self._connected:
            logger.info(f"Stopping MCP server: {self.server_name}")
            await self.exit_stack.aclose()
            self._connected = False
            self.session = None
            self._tools = []
    
    def is_connected(self) -> bool:
        """Check if connected."""
        return self._connected