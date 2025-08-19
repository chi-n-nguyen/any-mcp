"""
MCP-based ToolManager for llmgine Integration

This module provides a drop-in replacement for llmgine's ToolManager that uses
the Model Context Protocol (MCP) system for tool execution. It maintains the
same interface as the original ToolManager while providing enhanced capabilities
through MCP servers.
"""

import asyncio
import json
import logging
from typing import TYPE_CHECKING, Any, Callable, Dict, List, Optional, Union
from dataclasses import dataclass

from llmgine.llm import AsyncOrSyncToolFunction, SessionID
from llmgine.llm.tools.toolCall import ToolCall

# Import our MCP components
from any_mcp.managers.manager import MCPManager
from any_mcp.integration.message_bridge import MCPMessageBridge, create_standalone_bridge
from any_mcp.integration.tool_adapter import LLMgineToolAdapter

if TYPE_CHECKING:
    from llmgine.llm.context.memory import SimpleChatHistory

logger = logging.getLogger(__name__)


@dataclass
class MCPServerConfig:
    """Configuration for an MCP server."""
    name: str
    command: str
    args: List[str]
    env: Dict[str, str]
    auto_start: bool = True


class MCPToolManager:
    """
    MCP-based ToolManager that replaces llmgine's original ToolManager.
    
    This class provides the same interface as the original ToolManager but
    uses MCP servers for tool execution. It supports:
    - Direct function registration (legacy compatibility)
    - MCP server registration and tool discovery
    - Mixed execution environment (local functions + MCP tools)
    - Enhanced monitoring and lifecycle management
    """
    
    def __init__(self, chat_history: Optional["SimpleChatHistory"] = None, session_id: Optional[str] = None):
        """Initialize MCP-based tool manager."""
        self.chat_history = chat_history
        self.session_id = SessionID(session_id or "mcp_tool_manager")
        
        # Legacy compatibility - store directly registered functions
        self.local_tools: Dict[str, Callable] = {}
        self.local_tool_schemas: List[Dict[str, Any]] = []
        
        # MCP components
        self.mcp_manager: Optional[MCPManager] = None
        self.message_bridge: Optional[MCPMessageBridge] = None
        self.mcp_servers: Dict[str, MCPServerConfig] = {}
        
        # Combined tool registry
        self._tool_schemas: List[Dict[str, Any]] = []
        self._initialized = False
        
        logger.info(f"Initialized MCPToolManager with session {self.session_id}")
    
    async def initialize(self):
        """Initialize the MCP system."""
        if self._initialized:
            return
        
        try:
            # Initialize MCP manager
            self.mcp_manager = MCPManager()
            
            # Create message bridge (standalone mode for now)
            self.message_bridge = create_standalone_bridge(self.mcp_manager)
            
            self._initialized = True
            logger.info("MCP ToolManager initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize MCP ToolManager: {e}")
            raise
    
    async def ensure_initialized(self):
        """Ensure the MCP system is initialized."""
        if not self._initialized:
            await self.initialize()
    
    # ==================== Legacy ToolManager Interface ====================
    
    def register_tool(self, func: AsyncOrSyncToolFunction) -> None:
        """
        Register a function as a tool (legacy compatibility).
        
        This maintains compatibility with existing llmgine code that registers
        individual functions as tools.
        """
        name = func.__name__
        self.local_tools[name] = func
        
        # Generate OpenAI-format schema
        schema = self._generate_tool_schema(func)
        self.local_tool_schemas.append(schema)
        
        # Update combined schemas
        self._rebuild_tool_schemas()
        
        logger.info(f"Registered local tool: {name}")
    
    async def execute_tool_calls(self, tool_calls: List[ToolCall]) -> List[Any]:
        """Execute multiple tool calls."""
        await self.ensure_initialized()
        
        results = []
        for tool_call in tool_calls:
            result = await self.execute_tool_call(tool_call)
            results.append(result)
        
        return results
    
    async def execute_tool_call(self, tool_call: ToolCall) -> Any:
        """Execute a single tool call."""
        await self.ensure_initialized()
        
        tool_name = tool_call.name
        
        # Check if it's a local tool first
        if tool_name in self.local_tools:
            return await self._execute_local_tool(tool_call)
        
        # Try to execute as MCP tool
        return await self._execute_mcp_tool(tool_call)
    
    @property
    def tool_schemas(self) -> List[Dict[str, Any]]:
        """Get all tool schemas (local + MCP)."""
        return self._tool_schemas.copy()
    
    def chat_history_to_messages(self) -> List[Dict[str, Any]]:
        """Get messages from chat history for litellm."""
        if self.chat_history:
            return self.chat_history.get_messages()
        return []
    
    # ==================== MCP-Specific Methods ====================
    
    async def register_mcp_server(self, config: MCPServerConfig) -> bool:
        """
        Register and start an MCP server.
        
        Args:
            config: MCP server configuration
            
        Returns:
            True if server was successfully registered and started
        """
        await self.ensure_initialized()
        
        try:
            if config.auto_start:
                # Start the MCP server
                await self.mcp_manager.start_mcp(
                    config.name,
                    config.command,
                    config.args,
                    config.env
                )
                logger.info(f"Started MCP server: {config.name}")
            
            # Store configuration
            self.mcp_servers[config.name] = config
            
            # Refresh tool schemas
            await self._refresh_mcp_tools()
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to register MCP server {config.name}: {e}")
            return False
    
    async def register_mcp_servers(self, configs: List[MCPServerConfig]) -> Dict[str, bool]:
        """
        Register multiple MCP servers.
        
        Returns:
            Dictionary mapping server names to success status
        """
        results = {}
        for config in configs:
            results[config.name] = await self.register_mcp_server(config)
        return results
    
    async def discover_mcp_tools(self) -> List[Dict[str, Any]]:
        """
        Discover all available tools from MCP servers.
        
        Returns:
            List of tool information dictionaries
        """
        await self.ensure_initialized()
        
        if not self.message_bridge:
            return []
        
        try:
            tools = self.message_bridge.tool_adapter.list_available_tools()
            logger.info(f"Discovered {len(tools)} MCP tools")
            return tools
        except Exception as e:
            logger.error(f"Failed to discover MCP tools: {e}")
            return []
    
    async def get_mcp_server_status(self) -> Dict[str, Any]:
        """Get status of all MCP servers."""
        await self.ensure_initialized()
        
        if not self.mcp_manager:
            return {}
        
        status = {}
        for server_name in self.mcp_servers:
            client = self.mcp_manager.active_clients.get(server_name)
            status[server_name] = {
                "active": client is not None,
                "config": self.mcp_servers[server_name]
            }
        
        return status
    
    # ==================== Internal Methods ====================
    
    async def _execute_local_tool(self, tool_call: ToolCall) -> Any:
        """Execute a locally registered tool."""
        func = self.local_tools[tool_call.name]
        
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
            
            # Execute function
            if asyncio.iscoroutinefunction(func):
                result = await func(**args)
            else:
                result = func(**args)
            
            logger.debug(f"Executed local tool {tool_call.name} successfully")
            return result
            
        except Exception as e:
            error_msg = f"Error executing local tool {tool_call.name}: {str(e)}"
            logger.error(error_msg)
            return error_msg
    
    async def _execute_mcp_tool(self, tool_call: ToolCall) -> Any:
        """Execute an MCP tool."""
        if not self.message_bridge:
            return f"Error: MCP system not initialized for tool {tool_call.name}"
        
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
            
            # Find which MCP server has this tool
            mcp_name = await self._find_mcp_server_for_tool(tool_call.name)
            if not mcp_name:
                return f"Error: Tool '{tool_call.name}' not found in any MCP server"
            
            # Execute through message bridge
            result = await self.message_bridge.execute_tool(
                mcp_name=mcp_name,
                tool_name=tool_call.name,
                arguments=args,
                session_id=self.session_id
            )
            
            if result["success"]:
                logger.debug(f"Executed MCP tool {tool_call.name} successfully")
                return result["result"]
            else:
                error_msg = f"MCP tool execution failed: {result.get('error', 'Unknown error')}"
                logger.error(error_msg)
                return error_msg
                
        except Exception as e:
            error_msg = f"Error executing MCP tool {tool_call.name}: {str(e)}"
            logger.error(error_msg)
            return error_msg
    
    async def _find_mcp_server_for_tool(self, tool_name: str) -> Optional[str]:
        """Find which MCP server provides a specific tool."""
        try:
            tools = await self.discover_mcp_tools()
            for tool_info in tools:
                if tool_info["tool_name"] == tool_name:
                    return tool_info["mcp_name"]
        except Exception as e:
            logger.error(f"Error finding MCP server for tool {tool_name}: {e}")
        
        return None
    
    async def _refresh_mcp_tools(self):
        """Refresh the combined tool schemas from all sources."""
        await self.ensure_initialized()
        
        try:
            # Get MCP tool schemas
            mcp_tools = await self.discover_mcp_tools()
            mcp_schemas = []
            
            for tool_info in mcp_tools:
                schema = self._convert_mcp_tool_to_schema(tool_info)
                if schema:
                    mcp_schemas.append(schema)
            
            # Rebuild combined schemas
            self._tool_schemas = self.local_tool_schemas + mcp_schemas
            
            logger.info(f"Refreshed tool schemas: {len(self.local_tool_schemas)} local + {len(mcp_schemas)} MCP")
            
        except Exception as e:
            logger.error(f"Failed to refresh MCP tools: {e}")
    
    def _convert_mcp_tool_to_schema(self, tool_info: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Convert MCP tool info to OpenAI-format schema."""
        try:
            schema = {
                "type": "function",
                "function": {
                    "name": tool_info["tool_name"],
                    "description": tool_info.get("description", f"MCP tool from {tool_info['mcp_name']}"),
                    "parameters": tool_info.get("input_schema", {
                        "type": "object",
                        "properties": {},
                        "required": []
                    })
                }
            }
            return schema
        except Exception as e:
            logger.error(f"Failed to convert MCP tool to schema: {e}")
            return None
    
    def _generate_tool_schema(self, func: Callable) -> Dict[str, Any]:
        """Generate OpenAI-format tool schema from function (legacy compatibility)."""
        import inspect
        
        name = func.__name__
        doc = func.__doc__ or f"Function {name}"
        
        # Parse docstring for description
        lines = doc.strip().split('\n')
        description = lines[0] if lines else f"Function {name}"
        
        # Get function signature
        sig = inspect.signature(func)
        parameters = {
            "type": "object",
            "properties": {},
            "required": []
        }
        
        for param_name, param in sig.parameters.items():
            param_info = {
                "type": self._python_type_to_json_type(param.annotation),
                "description": f"Parameter {param_name}"
            }
            
            parameters["properties"][param_name] = param_info
            
            # Add to required if no default value
            if param.default == inspect.Parameter.empty:
                parameters["required"].append(param_name)
        
        return {
            "type": "function",
            "function": {
                "name": name,
                "description": description,
                "parameters": parameters
            }
        }
    
    def _python_type_to_json_type(self, python_type) -> str:
        """Convert Python type to JSON schema type."""
        if python_type == str or python_type == "str":
            return "string"
        elif python_type == int or python_type == "int":
            return "integer"
        elif python_type == float or python_type == "float":
            return "number"
        elif python_type == bool or python_type == "bool":
            return "boolean"
        elif python_type == list or python_type == "list":
            return "array"
        elif python_type == dict or python_type == "dict":
            return "object"
        else:
            return "string"  # Default fallback
    
    def _rebuild_tool_schemas(self):
        """Rebuild the combined tool schemas list."""
        # For now, just use local schemas
        # MCP schemas will be added when servers are registered
        self._tool_schemas = self.local_tool_schemas.copy()
    
    # ==================== Cleanup Methods ====================
    
    async def cleanup(self):
        """Clean up MCP resources."""
        try:
            if self.message_bridge:
                await self.message_bridge.cleanup()
            
            if self.mcp_manager:
                await self.mcp_manager.cleanup()
            
            logger.info("MCP ToolManager cleanup completed")
            
        except Exception as e:
            logger.error(f"Error during MCP ToolManager cleanup: {e}")
    
    # ==================== Backwards Compatibility ====================
    
    async def register_tool_async(self, func: AsyncOrSyncToolFunction) -> None:
        """Register tool async - for backwards compatibility."""
        self.register_tool(func)


# ==================== Convenience Functions ====================

def create_mcp_tool_manager(
    chat_history: Optional["SimpleChatHistory"] = None,
    session_id: Optional[str] = None,
    mcp_servers: Optional[List[MCPServerConfig]] = None
) -> MCPToolManager:
    """
    Create and configure an MCP ToolManager.
    
    Args:
        chat_history: Optional chat history for message context
        session_id: Optional session ID
        mcp_servers: Optional list of MCP server configurations
        
    Returns:
        Configured MCPToolManager instance
    """
    manager = MCPToolManager(chat_history, session_id)
    
    # Register MCP servers if provided
    if mcp_servers:
        async def setup_servers():
            await manager.register_mcp_servers(mcp_servers)
        
        # Store setup task for later execution
        manager._server_setup_task = setup_servers
    
    return manager


def create_default_mcp_servers() -> List[MCPServerConfig]:
    """
    Create default MCP server configurations.
    
    Returns:
        List of default MCP server configurations
    """
    return [
        MCPServerConfig(
            name="calculator",
            command="python",
            args=["mcps/demo_calculator.py"],
            env={},
            auto_start=True
        ),
        MCPServerConfig(
            name="notion",
            command="python", 
            args=["all_mcp_servers/notion_mcp_server.py"],
            env={},
            auto_start=True
        )
    ]


# ==================== Migration Helper ====================

class ToolManagerMigrationHelper:
    """Helper class for migrating from original ToolManager to MCPToolManager."""
    
    @staticmethod
    def migrate_from_original(original_manager, session_id: Optional[str] = None) -> MCPToolManager:
        """
        Migrate from original ToolManager to MCPToolManager.
        
        Args:
            original_manager: The original ToolManager instance
            session_id: Optional session ID for the new manager
            
        Returns:
            New MCPToolManager with migrated tools
        """
        # Create new MCP manager
        mcp_manager = MCPToolManager(original_manager.chat_history, session_id)
        
        # Migrate registered tools
        for tool_name, tool_func in original_manager.tools.items():
            mcp_manager.register_tool(tool_func)
        
        logger.info(f"Migrated {len(original_manager.tools)} tools to MCPToolManager")
        return mcp_manager
    
    @staticmethod
    def create_hybrid_manager(
        original_manager,
        mcp_servers: List[MCPServerConfig],
        session_id: Optional[str] = None
    ) -> MCPToolManager:
        """
        Create a hybrid manager with both original tools and MCP servers.
        
        Args:
            original_manager: The original ToolManager instance
            mcp_servers: List of MCP server configurations
            session_id: Optional session ID
            
        Returns:
            Hybrid MCPToolManager instance
        """
        # Migrate existing tools
        mcp_manager = ToolManagerMigrationHelper.migrate_from_original(
            original_manager, session_id
        )
        
        # Add MCP servers setup
        mcp_manager._server_configs = mcp_servers
        
        return mcp_manager
