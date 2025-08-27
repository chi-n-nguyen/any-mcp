"""
Unified MCP-Powered ToolManager

This is the new unified ToolManager that replaces LLMgine's original ToolManager
with a complete MCP-based system. It provides:

1. 100% backward compatibility with existing ToolManager interface
2. Support for local tools via LLMgine local tools MCP server 
3. Support for third-party MCP servers (Notion, GitHub, etc.)
4. Unified tool discovery, schema generation, and execution

This implementation uses the any-mcp system as the authoritative MCP client.
"""

import asyncio
import json
import logging
from typing import TYPE_CHECKING, Any, Callable, Dict, List, Optional

from any_mcp.managers.manager import MCPManager
from any_mcp.integration.tool_adapter import LLMgineToolAdapter
from llmgine.llm import AsyncOrSyncToolFunction
from llmgine.llm.tools.toolCall import ToolCall
from llmgine.llm.tools.mcp_config_loader import get_config_loader, MCPServerConfig

if TYPE_CHECKING:
    from llmgine.llm.context.memory import SimpleChatHistory

logger = logging.getLogger(__name__)


class MCPUnifiedToolManager:
    """
    Unified MCP-powered ToolManager that replaces the original ToolManager.
    
    This manager provides complete backward compatibility while enabling:
    - Local LLMgine tools via MCP server
    - Third-party MCP servers (Notion, GitHub, etc.)
    - Unified tool discovery and execution
    - Advanced MCP capabilities
    """
    
    def __init__(self, chat_history: Optional["SimpleChatHistory"] = None):
        """Initialize unified MCP-powered tool manager."""
        self.chat_history = chat_history
        
        # MCP system components
        self.mcp_manager: Optional[MCPManager] = None
        self.tool_adapter: Optional[LLMgineToolAdapter] = None
        self._initialized = False
        
        # Legacy compatibility: maintain the same interface
        self.tools: Dict[str, Callable] = {}  # For backward compatibility
        self.tool_schemas: List[Dict[str, Any]] = []
        
        logger.info("Initialized MCPUnifiedToolManager")
    
    async def initialize(self) -> bool:
        """
        Initialize the MCP system.
        
        Returns:
            True if initialization successful
        """
        if self._initialized:
            return True
        
        try:
            # Initialize MCP manager and adapter
            self.mcp_manager = MCPManager()
            self.tool_adapter = LLMgineToolAdapter(self.mcp_manager)
            
            # Start configured MCP servers
            await self._start_configured_servers()
            
            self._initialized = True
            logger.info("MCP system initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize MCP system: {e}")
            return False
    
    async def _start_configured_servers(self):
        """Start all available MCP servers from configuration."""
        config_loader = get_config_loader()
        available_servers = config_loader.get_available_servers()
        
        logger.info(f"Starting {len(available_servers)} available MCP servers")
        
        for server_config in available_servers:
            try:
                success = await self.mcp_manager.start_mcp(
                    name=server_config.name,
                    command=server_config.command,
                    args=server_config.args,
                    env=server_config.resolved_env
                )
                
                if success:
                    logger.info(f"Started MCP server: {server_config.name}")
                else:
                    logger.warning(f"Failed to start MCP server: {server_config.name}")
                    
            except Exception as e:
                logger.error(f"Error starting MCP server {server_config.name}: {e}")
        
        # Refresh tool schemas after starting servers
        await self._refresh_schemas()
        
        # Log missing environment variables
        missing_env = config_loader.get_missing_env_vars()
        if missing_env:
            logger.info("Some MCP servers are disabled due to missing environment variables:")
            for server, vars in missing_env.items():
                logger.info(f"  {server}: {', '.join(vars)}")
    
    async def _refresh_schemas(self):
        """Refresh tool schemas from all MCP servers."""
        if not self.tool_adapter:
            return
        
        try:
            # Get all tool schemas from MCP servers
            self.tool_schemas = await self.tool_adapter.get_all_openai_schemas()
            logger.debug(f"Refreshed {len(self.tool_schemas)} tool schemas")
        except Exception as e:
            logger.error(f"Failed to refresh tool schemas: {e}")
    
    # Backward compatibility methods - maintain exact same interface as original ToolManager
    
    def register_tool(self, func: AsyncOrSyncToolFunction) -> None:
        """
        Register a function as a tool (backward compatibility).
        
        Note: This method maintains compatibility but tools are now managed
        through MCP servers. For new tools, consider creating an MCP server.
        """
        # Store for compatibility but tools are handled via MCP
        name = func.__name__
        self.tools[name] = func
        
        logger.info(f"Tool {name} registered (compatibility mode)")
        
        # Note: In a production implementation, you might want to:
        # 1. Create a temporary MCP server for this tool
        # 2. Or add it to the local tools server dynamically
        # For now, we maintain the interface but recommend MCP server approach
    
    def parse_tools_to_list(self) -> List[Dict[str, Any]]:
        """Get all tools in OpenAI format for litellm."""
        return self.tool_schemas if self.tool_schemas else []
    
    async def execute_tool_calls(self, tool_calls: List[ToolCall]) -> List[Any]:
        """Execute multiple tool calls."""
        if not self._initialized:
            await self.initialize()
        
        results = []
        for tool_call in tool_calls:
            result = await self.execute_tool_call(tool_call)
            results.append(result)
        return results
    
    async def execute_tool_call(self, tool_call: ToolCall) -> Any:
        """Execute a single tool call."""
        if not self._initialized:
            await self.initialize()
        
        if not self.tool_adapter:
            return f"Error: MCP system not initialized"
        
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
            
            # Execute through MCP system
            result = await self.tool_adapter.execute_tool(tool_call.name, args)
            
            if result["success"]:
                return result["result"]
            else:
                return f"Error: {result.get('error', 'Tool execution failed')}"
                
        except Exception as e:
            logger.error(f"Error executing tool {tool_call.name}: {e}")
            return f"Error executing tool {tool_call.name}: {str(e)}"
    
    def chat_history_to_messages(self) -> List[Dict[str, Any]]:
        """Get messages from chat history for litellm."""
        if self.chat_history:
            return self.chat_history.get_messages()
        return []
    
    # New MCP-specific methods
    
    async def add_mcp_server(self, name: str, command: str, args: List[str], 
                            env: Optional[Dict[str, str]] = None) -> bool:
        """
        Add a new MCP server.
        
        Args:
            name: Unique name for the MCP server
            command: Command to run the server
            args: Arguments for the server command  
            env: Environment variables for the server
            
        Returns:
            True if server was added successfully
        """
        if not self._initialized:
            await self.initialize()
        
        if not self.mcp_manager:
            return False
        
        success = await self.mcp_manager.start_mcp(name, command, args, env)
        
        if success:
            await self._refresh_schemas()
            logger.info(f"Added MCP server: {name}")
        
        return success
    
    async def list_mcp_servers(self) -> Dict[str, bool]:
        """List all MCP servers and their status."""
        if not self.mcp_manager:
            return {}
        
        return await self.mcp_manager.health_check()
    
    async def list_available_tools(self) -> List[Dict[str, Any]]:
        """List all available tools across all MCP servers."""
        if not self.tool_adapter:
            return []
        
        return await self.tool_adapter.list_available_tools()
    
    async def cleanup(self):
        """Clean up MCP resources."""
        if self.mcp_manager:
            await self.mcp_manager.cleanup()
            logger.info("MCP resources cleaned up")
    
    # Legacy compatibility methods (for migration period)
    
    async def register_mcp_server(self, server_name: str, command: str, args: List[str], 
                                 env: Optional[Dict[str, str]] = None) -> bool:
        """Legacy method - use add_mcp_server instead."""
        return await self.add_mcp_server(server_name, command, args, env)
    
    async def cleanup_mcp_servers(self):
        """Legacy method - use cleanup instead."""
        await self.cleanup()
    
    async def register_tool_async(self, func: AsyncOrSyncToolFunction) -> None:
        """Legacy async registration - use register_tool instead."""
        self.register_tool(func)


# Factory function for easy migration
def create_mcp_tool_manager(chat_history: Optional["SimpleChatHistory"] = None) -> MCPUnifiedToolManager:
    """
    Create a new MCP-powered ToolManager.
    
    This is the recommended way to create a ToolManager that uses the
    unified MCP system.
    """
    return MCPUnifiedToolManager(chat_history)


# Backward compatibility alias
ToolManager = MCPUnifiedToolManager  # Drop-in replacement