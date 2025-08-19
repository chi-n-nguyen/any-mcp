"""
MCP Bridge Integration with llmgine MessageBus

This module provides integration between the MCP message bridge system
and llmgine's native MessageBus, enabling seamless event flow and
command handling across both systems.
"""

import asyncio
import logging
from typing import Any, Dict, Optional, Type, Union
from dataclasses import dataclass

# llmgine imports
from llmgine.bus.bus import MessageBus as LLMgineMessageBus
from llmgine.bus.interfaces import AsyncEventHandler, AsyncCommandHandler
from llmgine.messages.events import Event as LLMgineEvent
from llmgine.messages.commands import Command as LLMgineCommand, CommandResult
from llmgine.llm import SessionID

# MCP imports - using the bridge system we built
from any_mcp.managers.manager import MCPManager
from any_mcp.integration.message_bridge import (
    MCPMessageBridge,
    MCPEvent,
    MCPToolRegisteredEvent,
    MCPToolExecutionStartedEvent,
    MCPToolExecutionCompletedEvent,
    MCPServerConnectionEvent,
    ExecuteMCPToolCommand,
    RegisterMCPToolCommand,
    ListMCPToolsCommand
)
from any_mcp.integration.event_handlers import (
    MCPEventHandlers,
    MCPEventHandlerRegistry
)

logger = logging.getLogger(__name__)


# ==================== llmgine Event Extensions ====================

@dataclass
class MCPIntegrationEvent(LLMgineEvent):
    """Base class for MCP integration events in llmgine."""
    mcp_name: str = ""
    tool_name: str = ""


@dataclass
class MCPToolRegisteredLLMgineEvent(MCPIntegrationEvent):
    """llmgine event for MCP tool registration."""
    tool_schema: Dict[str, Any] = None
    registration_time: str = ""
    
    def __post_init__(self):
        super().__post_init__()
        if self.tool_schema is None:
            self.tool_schema = {}


@dataclass
class MCPToolExecutionLLMgineEvent(MCPIntegrationEvent):
    """llmgine event for MCP tool execution."""
    execution_id: str = ""
    tool_arguments: Dict[str, Any] = None
    success: bool = True
    result: Any = None
    error_message: Optional[str] = None
    execution_time_ms: Optional[float] = None
    
    def __post_init__(self):
        super().__post_init__()
        if self.tool_arguments is None:
            self.tool_arguments = {}


# ==================== llmgine Command Extensions ====================

@dataclass
class MCPIntegrationCommand(LLMgineCommand):
    """Base class for MCP integration commands in llmgine."""
    mcp_name: str = ""
    tool_name: str = ""


@dataclass
class ExecuteMCPToolLLMgineCommand(MCPIntegrationCommand):
    """llmgine command to execute an MCP tool."""
    tool_arguments: Dict[str, Any] = None
    execution_id: str = ""
    
    def __post_init__(self):
        super().__post_init__()
        if self.tool_arguments is None:
            self.tool_arguments = {}


@dataclass
class RegisterMCPServerCommand(MCPIntegrationCommand):
    """llmgine command to register an MCP server."""
    command: str = ""
    args: list = None
    env: Dict[str, str] = None
    auto_start: bool = True
    
    def __post_init__(self):
        super().__post_init__()
        if self.args is None:
            self.args = []
        if self.env is None:
            self.env = {}


# ==================== Bridge Integration Class ====================

class LLMgineMCPBridge:
    """
    Integration bridge between MCP system and llmgine MessageBus.
    
    This class provides:
    - Bidirectional event translation between MCP and llmgine
    - Command routing and execution
    - Lifecycle management for MCP servers
    - Event monitoring and metrics
    """
    
    def __init__(
        self,
        llmgine_bus: LLMgineMessageBus,
        session_id: Optional[Union[str, SessionID]] = None
    ):
        self.llmgine_bus = llmgine_bus
        self.session_id = SessionID(session_id) if isinstance(session_id, str) else (session_id or SessionID("mcp_bridge"))
        
        # MCP components
        self.mcp_manager: Optional[MCPManager] = None
        self.mcp_bridge: Optional[MCPMessageBridge] = None
        self.mcp_event_handlers: Optional[MCPEventHandlers] = None
        
        # Event translation mappings
        self.event_translators = {
            MCPToolRegisteredEvent: self._translate_tool_registered,
            MCPToolExecutionStartedEvent: self._translate_execution_started,
            MCPToolExecutionCompletedEvent: self._translate_execution_completed,
            MCPServerConnectionEvent: self._translate_server_connection
        }
        
        self._initialized = False
        logger.info(f"Created LLMgineMCPBridge with session {self.session_id}")
    
    async def initialize(self) -> bool:
        """Initialize the MCP bridge integration."""
        if self._initialized:
            return True
        
        try:
            # Initialize MCP manager
            self.mcp_manager = MCPManager()
            
            # Create MCP message bridge with llmgine bus integration
            from any_mcp.integration.message_bridge import create_bridge_with_bus
            self.mcp_bridge = create_bridge_with_bus(
                self.mcp_manager,
                self.llmgine_bus,
                str(self.session_id)
            )
            
            # Initialize event handlers
            self.mcp_event_handlers = MCPEventHandlers()
            
            # Register command handlers with llmgine bus
            self._register_llmgine_handlers()
            
            # Register event handlers with MCP bridge
            self._register_mcp_event_handlers()
            
            self._initialized = True
            logger.info("LLMgineMCPBridge initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize LLMgineMCPBridge: {e}")
            return False
    
    def _register_llmgine_handlers(self):
        """Register command handlers with llmgine MessageBus."""
        # Register MCP-specific commands
        self.llmgine_bus.register_command_handler(
            ExecuteMCPToolLLMgineCommand,
            self._handle_execute_mcp_tool_command,
            self.session_id
        )
        
        self.llmgine_bus.register_command_handler(
            RegisterMCPServerCommand,
            self._handle_register_mcp_server_command,
            self.session_id
        )
        
        logger.debug("Registered llmgine command handlers")
    
    def _register_mcp_event_handlers(self):
        """Register event handlers with MCP bridge."""
        if not self.mcp_bridge:
            return
        
        # Register event translators
        for mcp_event_type, translator in self.event_translators.items():
            self.mcp_bridge.add_event_handler(mcp_event_type, translator)
        
        # Register default MCP event handlers
        if self.mcp_event_handlers:
            self.mcp_bridge.add_event_handler(
                MCPToolRegisteredEvent,
                self.mcp_event_handlers.handle_tool_registered
            )
            self.mcp_bridge.add_event_handler(
                MCPToolExecutionStartedEvent,
                self.mcp_event_handlers.handle_execution_started
            )
            self.mcp_bridge.add_event_handler(
                MCPToolExecutionCompletedEvent,
                self.mcp_event_handlers.handle_execution_completed
            )
            self.mcp_bridge.add_event_handler(
                MCPServerConnectionEvent,
                self.mcp_event_handlers.handle_server_connection
            )
        
        logger.debug("Registered MCP event handlers")
    
    # ==================== Command Handlers ====================
    
    async def _handle_execute_mcp_tool_command(self, command: ExecuteMCPToolLLMgineCommand) -> CommandResult:
        """Handle MCP tool execution command from llmgine."""
        if not self.mcp_bridge:
            return CommandResult(
                success=False,
                command_id=command.command_id,
                error="MCP bridge not initialized"
            )
        
        try:
            # Execute through MCP bridge
            result = await self.mcp_bridge.execute_tool(
                mcp_name=command.mcp_name,
                tool_name=command.tool_name,
                arguments=command.tool_arguments,
                session_id=self.session_id
            )
            
            return CommandResult(
                success=result["success"],
                command_id=command.command_id,
                data={"result": result["result"]} if result["success"] else None,
                error=result.get("error") if not result["success"] else None
            )
            
        except Exception as e:
            logger.error(f"Error executing MCP tool {command.tool_name}: {e}")
            return CommandResult(
                success=False,
                command_id=command.command_id,
                error=f"Tool execution failed: {e}"
            )
    
    async def _handle_register_mcp_server_command(self, command: RegisterMCPServerCommand) -> CommandResult:
        """Handle MCP server registration command."""
        if not self.mcp_manager:
            return CommandResult(
                success=False,
                command_id=command.command_id,
                error="MCP manager not initialized"
            )
        
        try:
            # Start MCP server
            await self.mcp_manager.start_mcp(
                command.mcp_name,
                command.command,
                command.args,
                command.env
            )
            
            # Refresh tools in bridge
            if self.mcp_bridge:
                await self.mcp_bridge.register_all_tools(self.session_id)
            
            logger.info(f"Registered MCP server: {command.mcp_name}")
            
            return CommandResult(
                success=True,
                command_id=command.command_id,
                data={"server_name": command.mcp_name, "registered": True}
            )
            
        except Exception as e:
            logger.error(f"Error registering MCP server {command.mcp_name}: {e}")
            return CommandResult(
                success=False,
                command_id=command.command_id,
                error=f"Server registration failed: {e}"
            )
    
    # ==================== Event Translators ====================
    
    async def _translate_tool_registered(self, event: MCPToolRegisteredEvent):
        """Translate MCP tool registered event to llmgine event."""
        llmgine_event = MCPToolRegisteredLLMgineEvent(
            mcp_name=event.mcp_name,
            tool_name=event.tool_name,
            tool_schema=event.tool_schema,
            registration_time=event.registration_time,
            session_id=self.session_id
        )
        
        await self.llmgine_bus.publish(llmgine_event)
        logger.debug(f"Translated tool registered event: {event.tool_name}")
    
    async def _translate_execution_started(self, event: MCPToolExecutionStartedEvent):
        """Translate MCP execution started event to llmgine event."""
        llmgine_event = MCPToolExecutionLLMgineEvent(
            mcp_name=event.mcp_name,
            tool_name=event.tool_name,
            execution_id=event.execution_id,
            tool_arguments=event.tool_arguments,
            session_id=self.session_id
        )
        
        await self.llmgine_bus.publish(llmgine_event)
        logger.debug(f"Translated execution started event: {event.execution_id}")
    
    async def _translate_execution_completed(self, event: MCPToolExecutionCompletedEvent):
        """Translate MCP execution completed event to llmgine event."""
        llmgine_event = MCPToolExecutionLLMgineEvent(
            mcp_name=event.mcp_name,
            tool_name=event.tool_name,
            execution_id=event.execution_id,
            success=event.success,
            result=event.tool_result,
            error_message=event.error_message,
            execution_time_ms=event.execution_time_ms,
            session_id=self.session_id
        )
        
        await self.llmgine_bus.publish(llmgine_event)
        logger.debug(f"Translated execution completed event: {event.execution_id}")
    
    async def _translate_server_connection(self, event: MCPServerConnectionEvent):
        """Translate MCP server connection event to llmgine event."""
        # Create a generic integration event for server connection
        llmgine_event = MCPIntegrationEvent(
            mcp_name=event.mcp_name,
            tool_name="",  # Not tool-specific
            session_id=self.session_id
        )
        
        # Add connection status to metadata
        llmgine_event.metadata["connection_status"] = event.connection_status
        llmgine_event.metadata["server_info"] = event.server_info
        
        await self.llmgine_bus.publish(llmgine_event)
        logger.debug(f"Translated server connection event: {event.mcp_name} - {event.connection_status}")
    
    # ==================== High-Level Interface ====================
    
    async def register_mcp_server(
        self,
        name: str,
        command: str,
        args: list,
        env: Dict[str, str] = None
    ) -> bool:
        """
        Register and start an MCP server.
        
        Args:
            name: Server name
            command: Command to run server
            args: Command arguments
            env: Environment variables
            
        Returns:
            True if successful
        """
        if not self._initialized:
            await self.initialize()
        
        register_command = RegisterMCPServerCommand(
            mcp_name=name,
            command=command,
            args=args,
            env=env or {},
            session_id=self.session_id
        )
        
        result = await self.llmgine_bus.execute(register_command)
        return result.success
    
    async def execute_mcp_tool(
        self,
        mcp_name: str,
        tool_name: str,
        arguments: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Execute an MCP tool through llmgine bus.
        
        Args:
            mcp_name: MCP server name
            tool_name: Tool name
            arguments: Tool arguments
            
        Returns:
            Execution result
        """
        if not self._initialized:
            await self.initialize()
        
        execute_command = ExecuteMCPToolLLMgineCommand(
            mcp_name=mcp_name,
            tool_name=tool_name,
            tool_arguments=arguments,
            session_id=self.session_id
        )
        
        result = await self.llmgine_bus.execute(execute_command)
        
        return {
            "success": result.success,
            "result": result.data.get("result") if result.data else None,
            "error": result.error
        }
    
    async def get_available_tools(self) -> List[Dict[str, Any]]:
        """Get list of all available MCP tools."""
        if not (self.mcp_bridge and self._initialized):
            return []
        
        try:
            tools = self.mcp_bridge.tool_adapter.list_available_tools()
            return tools
        except Exception as e:
            logger.error(f"Error getting available tools: {e}")
            return []
    
    async def get_mcp_metrics(self) -> Dict[str, Any]:
        """Get MCP execution metrics."""
        if not (self.mcp_event_handlers and self._initialized):
            return {}
        
        try:
            return self.mcp_event_handlers.get_execution_metrics()
        except Exception as e:
            logger.error(f"Error getting MCP metrics: {e}")
            return {}
    
    async def get_server_status(self) -> Dict[str, Any]:
        """Get status of all MCP servers."""
        if not (self.mcp_manager and self._initialized):
            return {}
        
        try:
            status = {}
            for server_name, client in self.mcp_manager.active_clients.items():
                status[server_name] = {
                    "active": client is not None,
                    "connected": True  # If client exists, it's connected
                }
            return status
        except Exception as e:
            logger.error(f"Error getting server status: {e}")
            return {}
    
    # ==================== Cleanup ====================
    
    async def cleanup(self):
        """Clean up bridge resources."""
        try:
            if self.mcp_bridge:
                await self.mcp_bridge.cleanup()
            
            if self.mcp_event_handlers:
                await self.mcp_event_handlers.cleanup()
            
            if self.mcp_manager:
                await self.mcp_manager.cleanup()
            
            # Unregister handlers from llmgine bus
            self.llmgine_bus.unregister_session_handlers(self.session_id)
            
            logger.info("LLMgineMCPBridge cleanup completed")
            
        except Exception as e:
            logger.error(f"Error during bridge cleanup: {e}")


# ==================== Convenience Functions ====================

async def create_llmgine_mcp_integration(
    llmgine_bus: LLMgineMessageBus,
    session_id: Optional[str] = None,
    mcp_servers: Optional[List[Dict[str, Any]]] = None
) -> LLMgineMCPBridge:
    """
    Create and initialize a complete llmgine-MCP integration.
    
    Args:
        llmgine_bus: llmgine MessageBus instance
        session_id: Optional session ID
        mcp_servers: Optional list of MCP server configurations
        
    Returns:
        Initialized LLMgineMCPBridge
    """
    bridge = LLMgineMCPBridge(llmgine_bus, session_id)
    
    # Initialize the bridge
    success = await bridge.initialize()
    if not success:
        raise RuntimeError("Failed to initialize LLMgineMCPBridge")
    
    # Register MCP servers if provided
    if mcp_servers:
        for server_config in mcp_servers:
            await bridge.register_mcp_server(
                name=server_config["name"],
                command=server_config["command"],
                args=server_config["args"],
                env=server_config.get("env", {})
            )
    
    return bridge


def get_default_mcp_servers() -> List[Dict[str, Any]]:
    """Get default MCP server configurations."""
    return [
        {
            "name": "calculator",
            "command": "python",
            "args": ["mcps/demo_calculator.py"],
            "env": {}
        },
        {
            "name": "notion",
            "command": "python",
            "args": ["all_mcp_servers/notion_mcp_server.py"],
            "env": {}
        }
    ]

