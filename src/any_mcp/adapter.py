"""
Main AnyMCP adapter that can start any MCP and provide a unified interface.
"""

import asyncio
import subprocess
import json
from typing import Any, Dict, List, Optional, Union
from pathlib import Path

from .launcher import MCPLauncher
from .discovery import MCPDiscovery
from .normalizer import MCPNormalizer


class AnyMCP:
    """
    Universal MCP adapter that can start any MCP package and provide a unified interface.
    """
    
    def __init__(self, mcp_config: Union[str, Dict], timeout: int = 30):
        """
        Initialize the AnyMCP adapter.
        
        Args:
            mcp_config: Either a string path to MCP script, or a dict with command/args/env
            timeout: Timeout for MCP operations in seconds
        """
        self.mcp_config = mcp_config
        self.timeout = timeout
        self.launcher = MCPLauncher()
        self.discovery = MCPDiscovery()
        self.normalizer = MCPNormalizer()
        self.process = None
        self.tools = {}
        
    async def start(self):
        """Start the MCP process and discover available tools."""
        # Launch the MCP process
        self.process = await self.launcher.launch(self.mcp_config)
        
        # Discover available tools
        self.tools = await self.discovery.discover_tools(self.process)
        
        return self
        
    def list_tools(self) -> List[str]:
        """List all available tools from the MCP."""
        return list(self.tools.keys())
        
    async def call_tool(self, tool_name: str, **kwargs) -> Any:
        """
        Call a tool on the MCP.
        
        Args:
            tool_name: Name of the tool to call
            **kwargs: Arguments to pass to the tool
            
        Returns:
            The result from the tool
        """
        if tool_name not in self.tools:
            raise ValueError(f"Tool '{tool_name}' not found. Available tools: {list(self.tools.keys())}")
            
        # Call the tool through the launcher
        result = await self.launcher.call_tool(self.process, tool_name, kwargs)
        
        # Normalize the result
        return self.normalizer.normalize_result(result)
        
    async def stop(self):
        """Stop the MCP process."""
        if self.process:
            await self.launcher.stop(self.process)
            self.process = None
            
    async def __aenter__(self):
        await self.start()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.stop() 