"""
Message Bridge for llmgine Integration

This module provides a bridge between MCP tools and the llmgine message bus system,
enabling seamless integration and event handling across both systems.
"""

import asyncio
import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Callable, Type

# MCP imports
from mcp.types import Tool as MCPTool, CallToolResult, TextContent

# llmgine imports (optional)
try:
    from llmgine.bus.interfaces import IMessageBus, AsyncEventHandler
    from llmgine.messages.events import Event
    from llmgine.messages.commands import Command, CommandResult
    from llmgine.llm import SessionID
    LLMGINE_AVAILABLE = True
except ImportError:
    LLMGINE_AVAILABLE = False
    # Mock classes for when llmgine is not available
    class IMessageBus:
        pass
    class Event:
        pass
    class Command:
        pass
    class CommandResult:
        pass
    class SessionID:
        pass
    AsyncEventHandler = Callable

# any-mcp imports
from any_mcp.managers.manager import MCPManager
from any_mcp.integration.tool_adapter import LLMgineToolAdapter

logger = logging.getLogger(__name__)


# ==================== MCP Events for llmgine Bus ====================

@dataclass
class MCPEvent(Event):
    """Base class for MCP-related events in llmgine bus."""
    mcp_name: str = ""
    tool_name: str = ""
    
    def __post_init__(self):
        if LLMGINE_AVAILABLE:
            super().__post_init__()


@dataclass
class MCPToolRegisteredEvent(MCPEvent):
    """Event emitted when an MCP tool is registered."""
    tool_schema: Dict[str, Any] = field(default_factory=dict)
    registration_time: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class MCPToolExecutionStartedEvent(MCPEvent):
    """Event emitted when MCP tool execution starts."""
    tool_arguments: Dict[str, Any] = field(default_factory=dict)
    execution_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    start_time: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class MCPToolExecutionCompletedEvent(MCPEvent):
    """Event emitted when MCP tool execution completes."""
    execution_id: str = ""
    tool_result: Any = None
    success: bool = True
    error_message: Optional[str] = None
    execution_time_ms: Optional[float] = None
    end_time: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class MCPServerConnectionEvent(MCPEvent):
    """Event emitted when MCP server connection status changes."""
    connection_status: str = "unknown"  # connected, disconnected, error
    server_info: Dict[str, Any] = field(default_factory=dict)


# ==================== MCP Commands for llmgine Bus ====================

@dataclass
class MCPCommand(Command):
    """Base class for MCP-related commands in llmgine bus."""
    mcp_name: str = ""
    tool_name: str = ""


@dataclass
class ExecuteMCPToolCommand(MCPCommand):
    """Command to execute an MCP tool."""
    tool_arguments: Dict[str, Any] = field(default_factory=dict)
    execution_id: str = field(default_factory=lambda: str(uuid.uuid4()))


@dataclass
class RegisterMCPToolCommand(MCPCommand):
    """Command to register an MCP tool with the bridge."""
    tool_schema: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ListMCPToolsCommand(MCPCommand):
    """Command to list available MCP tools."""
    pass


# ==================== Message Bridge Implementation ====================

class MCPMessageBridge:
    """
    Bridge between MCP tools and llmgine message bus.
    
    This bridge handles:
    - Converting MCP tool operations to llmgine events and commands
    - Managing tool execution lifecycle through the message bus
    - Providing event-driven integration patterns
    """
    
    def __init__(
        self,
        mcp_manager: MCPManager,
        message_bus: Optional[IMessageBus] = None,
        session_id: Optional[SessionID] = None
    ):
        self.mcp_manager = mcp_manager
        self.message_bus = message_bus
        self.session_id = session_id or SessionID("MCP_BRIDGE")
        self.tool_adapter = LLMgineToolAdapter(mcp_manager)
        
        # Track active executions
        self.active_executions: Dict[str, Dict[str, Any]] = {}
        
        # Event handlers
        self.event_handlers: Dict[Type[Event], List[AsyncEventHandler]] = {}
        
        # Initialize if llmgine is available
        if LLMGINE_AVAILABLE and message_bus:
            self._register_command_handlers()
    
    def _register_command_handlers(self):
        """Register command handlers with the message bus."""
        if not (LLMGINE_AVAILABLE and self.message_bus):
            return
        
        # Register command handlers
        self.message_bus.register_command_handler(
            ExecuteMCPToolCommand,
            self._handle_execute_tool_command,
            self.session_id
        )
        
        self.message_bus.register_command_handler(
            RegisterMCPToolCommand,
            self._handle_register_tool_command,
            self.session_id
        )
        
        self.message_bus.register_command_handler(
            ListMCPToolsCommand,
            self._handle_list_tools_command,
            self.session_id
        )
    
    async def _handle_execute_tool_command(self, command: ExecuteMCPToolCommand) -> CommandResult:
        """Handle MCP tool execution command."""
        try:
            execution_id = command.execution_id
            start_time = datetime.now()
            
            # Track execution
            self.active_executions[execution_id] = {
                "mcp_name": command.mcp_name,
                "tool_name": command.tool_name,
                "start_time": start_time,
                "status": "running"
            }
            
            # Emit execution started event
            if self.message_bus:
                await self.message_bus.publish(
                    MCPToolExecutionStartedEvent(
                        mcp_name=command.mcp_name,
                        tool_name=command.tool_name,
                        tool_arguments=command.tool_arguments,
                        execution_id=execution_id,
                        session_id=command.session_id
                    )
                )
            
            # Execute the tool
            result = await self.mcp_manager.call_mcp(
                command.mcp_name,
                command.tool_name,
                command.tool_arguments
            )
            
            # Calculate execution time
            end_time = datetime.now()
            execution_time_ms = (end_time - start_time).total_seconds() * 1000
            
            # Update execution tracking
            self.active_executions[execution_id]["status"] = "completed"
            self.active_executions[execution_id]["end_time"] = end_time
            
            # Format result
            formatted_result = self.tool_adapter._format_tool_result(result) if result else None
            
            # Emit execution completed event
            if self.message_bus:
                await self.message_bus.publish(
                    MCPToolExecutionCompletedEvent(
                        mcp_name=command.mcp_name,
                        tool_name=command.tool_name,
                        execution_id=execution_id,
                        tool_result=formatted_result,
                        success=True,
                        execution_time_ms=execution_time_ms,
                        session_id=command.session_id
                    )
                )
            
            # Clean up execution tracking
            del self.active_executions[execution_id]
            
            return CommandResult(
                success=True,
                command_id=command.command_id,
                data={"result": formatted_result, "execution_id": execution_id}
            )
            
        except Exception as e:
            logger.error(f"Error executing MCP tool {command.tool_name}: {e}")
            
            # Update execution tracking
            if execution_id in self.active_executions:
                self.active_executions[execution_id]["status"] = "failed"
                self.active_executions[execution_id]["error"] = str(e)
            
            # Emit execution failed event
            if self.message_bus:
                await self.message_bus.publish(
                    MCPToolExecutionCompletedEvent(
                        mcp_name=command.mcp_name,
                        tool_name=command.tool_name,
                        execution_id=execution_id,
                        success=False,
                        error_message=str(e),
                        session_id=command.session_id
                    )
                )
            
            # Clean up execution tracking
            if execution_id in self.active_executions:
                del self.active_executions[execution_id]
            
            return CommandResult(
                success=False,
                command_id=command.command_id,
                error=f"Tool execution failed: {e}"
            )
    
    async def _handle_register_tool_command(self, command: RegisterMCPToolCommand) -> CommandResult:
        """Handle MCP tool registration command."""
        try:
            # Emit tool registered event
            if self.message_bus:
                await self.message_bus.publish(
                    MCPToolRegisteredEvent(
                        mcp_name=command.mcp_name,
                        tool_name=command.tool_name,
                        tool_schema=command.tool_schema,
                        session_id=command.session_id
                    )
                )
            
            return CommandResult(
                success=True,
                command_id=command.command_id,
                data={"registered": True}
            )
            
        except Exception as e:
            logger.error(f"Error registering MCP tool {command.tool_name}: {e}")
            return CommandResult(
                success=False,
                command_id=command.command_id,
                error=f"Tool registration failed: {e}"
            )
    
    async def _handle_list_tools_command(self, command: ListMCPToolsCommand) -> CommandResult:
        """Handle list MCP tools command."""
        try:
            tools = self.tool_adapter.list_available_tools()
            
            return CommandResult(
                success=True,
                command_id=command.command_id,
                data={"tools": tools}
            )
            
        except Exception as e:
            logger.error(f"Error listing MCP tools: {e}")
            return CommandResult(
                success=False,
                command_id=command.command_id,
                error=f"Failed to list tools: {e}"
            )
    
    # ==================== Event Management ====================
    
    def add_event_handler(self, event_type: Type[Event], handler: AsyncEventHandler):
        """Add an event handler for a specific event type."""
        if event_type not in self.event_handlers:
            self.event_handlers[event_type] = []
        
        self.event_handlers[event_type].append(handler)
        
        # Register with message bus if available
        if LLMGINE_AVAILABLE and self.message_bus:
            self.message_bus.register_event_handler(
                event_type,
                handler,
                self.session_id
            )
    
    def remove_event_handler(self, event_type: Type[Event], handler: AsyncEventHandler):
        """Remove an event handler for a specific event type."""
        if event_type in self.event_handlers:
            try:
                self.event_handlers[event_type].remove(handler)
                if not self.event_handlers[event_type]:
                    del self.event_handlers[event_type]
            except ValueError:
                pass
    
    async def emit_event(self, event: MCPEvent):
        """Emit an event through the message bus."""
        if LLMGINE_AVAILABLE and self.message_bus:
            await self.message_bus.publish(event)
        else:
            # Fallback: call handlers directly
            event_type = type(event)
            if event_type in self.event_handlers:
                for handler in self.event_handlers[event_type]:
                    try:
                        await handler(event)
                    except Exception as e:
                        logger.error(f"Error in event handler: {e}")
    
    # ==================== High-Level Integration Methods ====================
    
    async def execute_tool(
        self,
        mcp_name: str,
        tool_name: str,
        arguments: Dict[str, Any],
        session_id: Optional[SessionID] = None
    ) -> Dict[str, Any]:
        """
        Execute an MCP tool through the message bus.
        
        Args:
            mcp_name: Name of the MCP server
            tool_name: Name of the tool
            arguments: Tool arguments
            session_id: Optional session ID
            
        Returns:
            Tool execution result
        """
        if not (LLMGINE_AVAILABLE and self.message_bus):
            # Fallback to direct execution
            result = await self.mcp_manager.call_mcp(mcp_name, tool_name, arguments)
            return {
                "result": self.tool_adapter._format_tool_result(result) if result else None,
                "success": True
            }
        
        # Execute through message bus
        command = ExecuteMCPToolCommand(
            mcp_name=mcp_name,
            tool_name=tool_name,
            tool_arguments=arguments,
            session_id=session_id or self.session_id
        )
        
        result = await self.message_bus.execute(command)
        
        return {
            "result": result.data.get("result") if result.data else None,
            "success": result.success,
            "error": result.error if not result.success else None
        }
    
    async def register_all_tools(self, session_id: Optional[SessionID] = None):
        """Register all available MCP tools with the bridge."""
        tools = self.tool_adapter.list_available_tools()
        
        for tool_info in tools:
            try:
                if LLMGINE_AVAILABLE and self.message_bus:
                    command = RegisterMCPToolCommand(
                        mcp_name=tool_info["mcp_name"],
                        tool_name=tool_info["tool_name"],
                        tool_schema=tool_info.get("input_schema", {}),
                        session_id=session_id or self.session_id
                    )
                    
                    await self.message_bus.execute(command)
                else:
                    # Emit event directly
                    await self.emit_event(
                        MCPToolRegisteredEvent(
                            mcp_name=tool_info["mcp_name"],
                            tool_name=tool_info["tool_name"],
                            tool_schema=tool_info.get("input_schema", {}),
                            session_id=session_id or self.session_id
                        )
                    )
                    
            except Exception as e:
                logger.error(f"Failed to register tool {tool_info['tool_name']}: {e}")
    
    async def get_execution_status(self, execution_id: str) -> Optional[Dict[str, Any]]:
        """Get the status of a tool execution."""
        return self.active_executions.get(execution_id)
    
    def get_active_executions(self) -> Dict[str, Dict[str, Any]]:
        """Get all active executions."""
        return self.active_executions.copy()
    
    async def cleanup(self):
        """Clean up bridge resources."""
        # Cancel any active executions
        for execution_id in list(self.active_executions.keys()):
            self.active_executions[execution_id]["status"] = "cancelled"
        
        # Clear event handlers
        self.event_handlers.clear()
        
        # Unregister from message bus
        if LLMGINE_AVAILABLE and self.message_bus:
            self.message_bus.unregister_session_handlers(self.session_id)


# ==================== Utility Functions ====================

def create_bridge_with_bus(
    mcp_manager: MCPManager,
    message_bus: IMessageBus,
    session_id: Optional[str] = None
) -> MCPMessageBridge:
    """
    Create an MCP message bridge with llmgine bus integration.
    
    Args:
        mcp_manager: MCP manager instance
        message_bus: llmgine message bus instance
        session_id: Optional session ID
        
    Returns:
        Configured MCPMessageBridge instance
    """
    if not LLMGINE_AVAILABLE:
        raise RuntimeError("llmgine is not available for message bus integration")
    
    session = SessionID(session_id) if session_id else SessionID("MCP_BRIDGE")
    bridge = MCPMessageBridge(mcp_manager, message_bus, session)
    
    return bridge


def create_standalone_bridge(mcp_manager: MCPManager) -> MCPMessageBridge:
    """
    Create a standalone MCP message bridge without llmgine bus integration.
    
    Args:
        mcp_manager: MCP manager instance
        
    Returns:
        Configured MCPMessageBridge instance
    """
    return MCPMessageBridge(mcp_manager, None, None)
