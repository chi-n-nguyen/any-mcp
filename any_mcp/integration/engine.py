"""
llmgine Engine Integration for any-mcp

This module provides a llmgine-compatible engine that wraps any-mcp functionality,
allowing seamless integration with llmgine's message bus and tool management systems.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Type
from contextlib import AsyncExitStack

# llmgine imports (will be optional)
try:
    from llmgine.llm.engine.engine import Engine
    from llmgine.messages.commands import Command, CommandResult
    from llmgine.messages.events import Status, ToolResult
    from llmgine.bus.bus import MessageBus
    from llmgine.llm.tools.tool import Tool as LLMgineTool
    LLMGINE_AVAILABLE = True
except ImportError:
    LLMGINE_AVAILABLE = False
    # Mock classes for when llmgine is not available
    class Engine:
        pass
    class Command:
        pass
    class CommandResult:
        pass
    class Status:
        pass
    class ToolResult:
        pass
    class MessageBus:
        pass
    class LLMgineTool:
        pass

# any-mcp imports
from any_mcp.managers.manager import MCPManager
from any_mcp.core.client import MCPClient
from any_mcp.integration.tool_adapter import LLMgineToolAdapter
from any_mcp.integration.message_bridge import MessageBridge

logger = logging.getLogger(__name__)


class AnyMCPCommand(Command):
    """Command for executing MCP tool calls through any-mcp."""
    
    def __init__(self, mcp_name: str, tool_name: str, arguments: Dict[str, Any], session_id: str):
        self.mcp_name = mcp_name
        self.tool_name = tool_name
        self.arguments = arguments
        self.session_id = session_id


class AnyMCPEngine(Engine):
    """
    llmgine-compatible engine that wraps any-mcp functionality.
    
    This engine allows any-mcp to function as a llmgine engine, providing:
    - MCP tool discovery and execution
    - Integration with llmgine's message bus
    - Tool result handling and status updates
    - Session management
    """
    
    def __init__(self, session_id: str, config_path: str = "config/mcp_config.yaml"):
        if not LLMGINE_AVAILABLE:
            raise ImportError("llmgine is required for AnyMCPEngine. Install with: pip install llmgine")
        
        self.session_id = session_id
        self.config_path = config_path
        self.mcp_manager: Optional[MCPManager] = None
        self.tool_adapter: Optional[LLMgineToolAdapter] = None
        self.message_bridge: Optional[MessageBridge] = None
        self.bus: Optional[MessageBus] = None
        self.exit_stack = AsyncExitStack()
        self._initialized = False
        
        # Track registered tools
        self.registered_tools: Dict[str, LLMgineTool] = {}
        
    async def initialize(self, bus: MessageBus):
        """Initialize the engine with llmgine message bus."""
        try:
            self.bus = bus
            
            # Initialize MCP manager
            self.mcp_manager = MCPManager(self.config_path)
            await self.exit_stack.enter_async_context(self.mcp_manager)
            
            # Initialize tool adapter
            self.tool_adapter = LLMgineToolAdapter(self.mcp_manager)
            
            # Initialize message bridge
            self.message_bridge = MessageBridge(self.bus, self.session_id)
            
            # Discover and register MCP tools
            await self._discover_and_register_tools()
            
            self._initialized = True
            logger.info(f"AnyMCPEngine initialized successfully for session {self.session_id}")
            
        except Exception as e:
            logger.error(f"Failed to initialize AnyMCPEngine: {e}")
            raise
    
    async def _discover_and_register_tools(self):
        """Discover MCP tools and register them with llmgine."""
        if not self.mcp_manager or not self.tool_adapter:
            return
        
        try:
            # Get all available MCPs
            active_mcps = self.mcp_manager.get_active_mcps()
            
            for mcp_name in active_mcps:
                try:
                    # Get tools from MCP
                    client = self.mcp_manager.active_clients.get(mcp_name)
                    if client:
                        tools = await client.list_tools()
                        
                        # Convert and register each tool
                        for tool in tools:
                            llmgine_tool = self.tool_adapter.convert_mcp_tool(tool, mcp_name)
                            if llmgine_tool:
                                tool_key = f"{mcp_name}:{tool.name}"
                                self.registered_tools[tool_key] = llmgine_tool
                                
                                # Publish tool registration event
                                await self.message_bridge.publish_tool_registered(tool_key, llmgine_tool)
                                
                except Exception as e:
                    logger.warning(f"Failed to discover tools from MCP {mcp_name}: {e}")
                    
        except Exception as e:
            logger.error(f"Failed to discover MCP tools: {e}")
    
    async def handle_command(self, cmd: AnyMCPCommand) -> CommandResult:
        """Handle MCP tool execution commands."""
        if not self._initialized:
            return CommandResult(success=False, result="Engine not initialized")
        
        try:
            # Publish status update
            await self.message_bridge.publish_status("executing_tool", {
                "mcp": cmd.mcp_name,
                "tool": cmd.tool_name,
                "arguments": cmd.arguments
            })
            
            # Execute the tool through MCP manager
            if not self.mcp_manager:
                return CommandResult(success=False, result="MCP manager not available")
            
            result = await self.mcp_manager.call_mcp(cmd.mcp_name, cmd.tool_name, cmd.arguments)
            
            if result:
                # Convert result to llmgine format
                tool_result = self.tool_adapter.convert_tool_result(result, cmd.mcp_name, cmd.tool_name)
                
                # Publish tool result event
                await self.message_bridge.publish_tool_result(tool_result)
                
                # Publish completion status
                await self.message_bridge.publish_status("tool_completed", {
                    "mcp": cmd.mcp_name,
                    "tool": cmd.tool_name,
                    "success": True
                })
                
                return CommandResult(success=True, result=tool_result)
            else:
                # Publish error status
                await self.message_bridge.publish_status("tool_failed", {
                    "mcp": cmd.mcp_name,
                    "tool": cmd.tool_name,
                    "error": "Tool execution failed"
                })
                
                return CommandResult(success=False, result="Tool execution failed")
                
        except Exception as e:
            logger.error(f"Error executing MCP tool: {e}")
            
            # Publish error status
            await self.message_bridge.publish_status("tool_error", {
                "mcp": cmd.mcp_name,
                "tool": cmd.tool_name,
                "error": str(e)
            })
            
            return CommandResult(success=False, result=f"Error: {str(e)}")
    
    async def get_available_tools(self) -> List[LLMgineTool]:
        """Get list of available MCP tools as llmgine tools."""
        return list(self.registered_tools.values())
    
    async def execute_tool(self, mcp_name: str, tool_name: str, arguments: Dict[str, Any]) -> Any:
        """Execute a specific MCP tool."""
        cmd = AnyMCPCommand(mcp_name, tool_name, arguments, self.session_id)
        result = await self.handle_command(cmd)
        
        if result.success:
            return result.result
        else:
            raise RuntimeError(f"Tool execution failed: {result.result}")
    
    async def cleanup(self):
        """Clean up engine resources."""
        try:
            if self.exit_stack:
                await self.exit_stack.aclose()
            
            self._initialized = False
            logger.info(f"AnyMCPEngine cleaned up for session {self.session_id}")
            
        except Exception as e:
            logger.error(f"Error during engine cleanup: {e}")
    
    async def __aenter__(self):
        """Async context manager entry."""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.cleanup()


# Factory function for easy engine creation
async def create_any_mcp_engine(session_id: str, config_path: str = "config/mcp_config.yaml") -> AnyMCPEngine:
    """Create and initialize an AnyMCPEngine instance."""
    engine = AnyMCPEngine(session_id, config_path)
    return engine
