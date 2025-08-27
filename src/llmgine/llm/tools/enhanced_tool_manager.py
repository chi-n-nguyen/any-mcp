"""
Enhanced Tool Manager with MCP Integration

This module provides an enhanced ToolManager that maintains backward compatibility
with the existing llmgine ToolManager while adding powerful MCP capabilities.
"""

import asyncio
import inspect
import json
import logging
from typing import TYPE_CHECKING, Any, Callable, Dict, List, Optional

from llmgine.llm import AsyncOrSyncToolFunction
from llmgine.llm.tools.toolCall import ToolCall
from llmgine.llm.tools.tool_manager import ToolManager

# Import our any-mcp components
from any_mcp.managers.manager import MCPManager
from any_mcp.integration.tool_adapter import LLMgineToolAdapter

if TYPE_CHECKING:
    from llmgine.llm.context.memory import SimpleChatHistory

logger = logging.getLogger(__name__)


class EnhancedToolManager(ToolManager):
    """
    Enhanced ToolManager with MCP integration.
    
    This class extends the original ToolManager to provide:
    - Backward compatibility with existing local tools
    - MCP server integration for external tools
    - Unified tool execution interface
    - Advanced tool discovery and management
    """
    
    def __init__(self, chat_history: Optional["SimpleChatHistory"] = None):
        """Initialize enhanced tool manager."""
        # Initialize parent class
        super().__init__(chat_history)
        
        # MCP components
        self.mcp_manager: Optional[MCPManager] = None
        self.tool_adapter: Optional[LLMgineToolAdapter] = None
        self._mcp_initialized = False
        
        # Combined tool tracking
        self._mcp_tools_cache: List[Dict[str, Any]] = []
        
        logger.info("Initialized EnhancedToolManager with MCP support")
    
    async def initialize_mcp(self) -> bool:
        """
        Initialize MCP system.
        
        Returns:
            True if initialization was successful
        """
        if self._mcp_initialized:
            return True
        
        try:
            # Initialize MCP manager
            self.mcp_manager = MCPManager()
            self.tool_adapter = LLMgineToolAdapter(self.mcp_manager)
            
            self._mcp_initialized = True
            logger.info("MCP system initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize MCP system: {e}")
            return False
    
    async def add_mcp_server(self, name: str, command: str, args: List[str], env: Optional[Dict[str, str]] = None) -> bool:
        """
        Add and start an MCP server.
        
        Args:
            name: Unique name for the MCP server
            command: Command to run the server
            args: Arguments for the server command
            env: Environment variables for the server
            
        Returns:
            True if server was added successfully
        """
        # Ensure MCP is initialized
        if not self._mcp_initialized:
            await self.initialize_mcp()
        
        if not self.mcp_manager:
            logger.error("MCP manager not initialized")
            return False
        
        # Start the MCP server
        success = await self.mcp_manager.start_mcp(name, command, args, env)
        
        if success:
            # Refresh tool schemas
            await self._refresh_mcp_tools()
            logger.info(f"Added MCP server: {name}")
        
        return success
    
    async def _refresh_mcp_tools(self):
        """Refresh MCP tools and update combined tool schemas."""
        if not self.tool_adapter:
            return
        
        try:
            # Get MCP tool schemas
            mcp_schemas = await self.tool_adapter.get_all_openai_schemas()
            
            # Update combined tool schemas
            self.tool_schemas = self._get_local_schemas() + mcp_schemas
            
            # Cache MCP tools info
            self._mcp_tools_cache = await self.tool_adapter.list_available_tools()
            
            logger.debug(f"Refreshed {len(mcp_schemas)} MCP tool schemas")
            
        except Exception as e:
            logger.error(f"Failed to refresh MCP tools: {e}")
    
    def _get_local_schemas(self) -> List[Dict[str, Any]]:
        """Get schemas for local (non-MCP) tools."""
        local_schemas = []
        
        for tool_name, tool_func in self.tools.items():
            try:
                schema = self._generate_tool_schema(tool_func)
                local_schemas.append(schema)
            except Exception as e:
                logger.error(f"Failed to generate schema for local tool {tool_name}: {e}")
        
        return local_schemas
    
    def register_tool(self, func: AsyncOrSyncToolFunction) -> None:
        """Register a function as a tool (maintains backward compatibility)."""
        # Call parent method
        super().register_tool(func)
        
        # If MCP is initialized, refresh combined schemas
        if self._mcp_initialized:
            asyncio.create_task(self._refresh_mcp_tools())
    
    async def execute_tool_call(self, tool_call: ToolCall) -> Any:
        """Execute a single tool call (enhanced with MCP support)."""
        tool_name = tool_call.name
        
        # Check if it's a local tool first
        if tool_name in self.tools:
            return await super().execute_tool_call(tool_call)
        
        # Try to execute as MCP tool
        if self._mcp_initialized and self.tool_adapter:
            return await self._execute_mcp_tool(tool_call)
        
        # Tool not found
        return f"Error: Tool '{tool_name}' not found"
    
    async def _execute_mcp_tool(self, tool_call: ToolCall) -> Any:
        """Execute an MCP tool."""
        if not self.tool_adapter:
            return "Error: MCP system not initialized"
        
        try:
            # Parse arguments
            if isinstance(tool_call.arguments, str):
                if tool_call.arguments.strip() == "":
                    args = {}
                else:
                    args = json.loads(tool_call.arguments)
            else:
                args = tool_call.arguments
            
            # Handle empty/None arguments
            if not args:
                args = {}
            
            # Execute through tool adapter
            result = await self.tool_adapter.execute_tool(tool_call.name, args)
            
            if result["success"]:
                return result["result"]
            else:
                return f"Error: {result.get('error', 'MCP tool execution failed')}"
                
        except Exception as e:
            logger.error(f"Error executing MCP tool {tool_call.name}: {e}")
            return f"Error executing MCP tool {tool_call.name}: {str(e)}"
    
    def parse_tools_to_list(self) -> List[Dict[str, Any]]:
        """Get all tools in OpenAI format for litellm (enhanced with MCP tools)."""
        return self.tool_schemas if self.tool_schemas else []
    
    async def list_all_tools(self) -> Dict[str, Any]:
        """
        List all available tools (local + MCP).
        
        Returns:
            Dictionary with tool information
        """
        local_tools = list(self.tools.keys())
        mcp_tools = self._mcp_tools_cache.copy()
        
        # Get MCP server status
        mcp_servers = {}
        if self.mcp_manager:
            mcp_servers = {
                name: client.is_connected() 
                for name, client in self.mcp_manager.active_clients.items()
            }
        
        return {
            "local_tools": local_tools,
            "mcp_tools": mcp_tools,
            "mcp_servers": mcp_servers,
            "total_schemas": len(self.tool_schemas)
        }
    
    async def get_mcp_server_status(self) -> Dict[str, bool]:
        """Get status of all MCP servers."""
        if not self.mcp_manager:
            return {}
        
        return await self.mcp_manager.health_check()
    
    def is_mcp_tool(self, tool_name: str) -> bool:
        """Check if a tool name corresponds to an MCP tool."""
        return any(
            tool["tool_name"] == tool_name or f"{tool['mcp_name']}_{tool['tool_name']}" == tool_name
            for tool in self._mcp_tools_cache
        )
    
    def is_local_tool(self, tool_name: str) -> bool:
        """Check if a tool name corresponds to a local tool."""
        return tool_name in self.tools
    
    async def cleanup(self):
        """Clean up MCP resources."""
        if self.mcp_manager:
            await self.mcp_manager.cleanup()
            logger.info("MCP resources cleaned up")


class MCPServerConfig:
    """Configuration for an MCP server."""
    
    def __init__(self, name: str, command: str, args: List[str], env: Optional[Dict[str, str]] = None):
        self.name = name
        self.command = command
        self.args = args
        self.env = env or {}


async def create_enhanced_tool_manager_with_servers(
    chat_history: Optional["SimpleChatHistory"] = None,
    mcp_servers: Optional[List[MCPServerConfig]] = None
) -> EnhancedToolManager:
    """
    Create an enhanced tool manager with MCP servers.
    
    Args:
        chat_history: Optional chat history
        mcp_servers: List of MCP server configurations
        
    Returns:
        Configured EnhancedToolManager
    """
    manager = EnhancedToolManager(chat_history)
    
    # Initialize MCP
    await manager.initialize_mcp()
    
    # Add MCP servers
    if mcp_servers:
        for server_config in mcp_servers:
            await manager.add_mcp_server(
                server_config.name,
                server_config.command,
                server_config.args,
                server_config.env
            )
    
    return manager


def get_default_mcp_servers() -> List[MCPServerConfig]:
    """Get default MCP server configurations."""
    return [
        MCPServerConfig(
            name="calculator",
            command="python",
            args=["mcps/demo_calculator.py"],
            env={}
        )
    ]

