"""
Tests for MCP Message Bridge Integration

This module tests the message bridge functionality between MCP tools
and the llmgine message bus system.
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Dict, Any, List

# Test imports
from any_mcp.integration.message_bridge import (
    MCPMessageBridge,
    MCPEvent,
    MCPToolRegisteredEvent,
    MCPToolExecutionStartedEvent,
    MCPToolExecutionCompletedEvent,
    MCPServerConnectionEvent,
    ExecuteMCPToolCommand,
    RegisterMCPToolCommand,
    ListMCPToolsCommand,
    create_standalone_bridge
)
from any_mcp.integration.event_handlers import (
    MCPEventHandlerRegistry,
    MCPToolExecutionTracker,
    MCPEventHandlers,
    setup_event_registry_with_defaults
)
from any_mcp.managers.manager import MCPManager
from any_mcp.integration.tool_adapter import LLMgineToolAdapter

# Mock llmgine components for testing
class MockMessageBus:
    def __init__(self):
        self.commands = []
        self.events = []
        self.handlers = {}
        self.running = True
    
    async def execute(self, command):
        self.commands.append(command)
        # Mock successful execution
        from any_mcp.integration.message_bridge import CommandResult
        return CommandResult(
            success=True,
            command_id=command.command_id,
            data={"result": "mock_result"}
        )
    
    async def publish(self, event):
        self.events.append(event)
    
    def register_command_handler(self, command_type, handler, session_id):
        self.handlers[command_type.__name__] = handler
    
    def register_event_handler(self, event_type, handler, session_id):
        pass
    
    def unregister_session_handlers(self, session_id):
        pass


class MockSessionID:
    def __init__(self, value):
        self.value = value


@pytest.fixture
def mock_mcp_manager():
    """Create a mock MCP manager."""
    manager = AsyncMock(spec=MCPManager)
    manager.active_clients = {"test_server": AsyncMock()}
    manager.call_mcp = AsyncMock(return_value=AsyncMock(
        content=[AsyncMock(text="test result")],
        isError=False
    ))
    return manager


@pytest.fixture
def mock_message_bus():
    """Create a mock message bus."""
    return MockMessageBus()


@pytest.fixture
def message_bridge(mock_mcp_manager, mock_message_bus):
    """Create a message bridge for testing."""
    with patch('any_mcp.integration.message_bridge.LLMGINE_AVAILABLE', True):
        with patch('any_mcp.integration.message_bridge.SessionID', MockSessionID):
            bridge = MCPMessageBridge(
                mock_mcp_manager,
                mock_message_bus,
                MockSessionID("TEST_SESSION")
            )
            return bridge


@pytest.fixture
def standalone_bridge(mock_mcp_manager):
    """Create a standalone message bridge for testing."""
    return create_standalone_bridge(mock_mcp_manager)


class TestMCPMessageBridge:
    """Test cases for MCPMessageBridge."""
    
    def test_bridge_initialization(self, message_bridge, mock_mcp_manager, mock_message_bus):
        """Test bridge initialization."""
        assert message_bridge.mcp_manager == mock_mcp_manager
        assert message_bridge.message_bus == mock_message_bus
        assert message_bridge.session_id.value == "TEST_SESSION"
        assert isinstance(message_bridge.tool_adapter, LLMgineToolAdapter)
        assert message_bridge.active_executions == {}
    
    def test_standalone_bridge_initialization(self, standalone_bridge, mock_mcp_manager):
        """Test standalone bridge initialization."""
        assert standalone_bridge.mcp_manager == mock_mcp_manager
        assert standalone_bridge.message_bus is None
        assert standalone_bridge.session_id is None
    
    @pytest.mark.asyncio
    async def test_execute_tool_command_success(self, message_bridge, mock_mcp_manager):
        """Test successful tool execution command."""
        command = ExecuteMCPToolCommand(
            mcp_name="test_server",
            tool_name="test_tool",
            tool_arguments={"arg1": "value1"},
            session_id=MockSessionID("TEST_SESSION")
        )
        
        result = await message_bridge._handle_execute_tool_command(command)
        
        assert result.success
        assert "result" in result.data
        assert "execution_id" in result.data
        mock_mcp_manager.call_mcp.assert_called_once_with(
            "test_server",
            "test_tool",
            {"arg1": "value1"}
        )
    
    @pytest.mark.asyncio
    async def test_execute_tool_command_failure(self, message_bridge, mock_mcp_manager):
        """Test failed tool execution command."""
        mock_mcp_manager.call_mcp.side_effect = Exception("Tool execution failed")
        
        command = ExecuteMCPToolCommand(
            mcp_name="test_server",
            tool_name="test_tool",
            tool_arguments={"arg1": "value1"},
            session_id=MockSessionID("TEST_SESSION")
        )
        
        result = await message_bridge._handle_execute_tool_command(command)
        
        assert not result.success
        assert "Tool execution failed" in result.error
    
    @pytest.mark.asyncio
    async def test_register_tool_command(self, message_bridge):
        """Test tool registration command."""
        command = RegisterMCPToolCommand(
            mcp_name="test_server",
            tool_name="test_tool",
            tool_schema={"type": "object"},
            session_id=MockSessionID("TEST_SESSION")
        )
        
        result = await message_bridge._handle_register_tool_command(command)
        
        assert result.success
        assert result.data["registered"]
    
    @pytest.mark.asyncio
    async def test_list_tools_command(self, message_bridge):
        """Test list tools command."""
        with patch.object(message_bridge.tool_adapter, 'list_available_tools') as mock_list:
            mock_list.return_value = [
                {"mcp_name": "test_server", "tool_name": "test_tool"}
            ]
            
            command = ListMCPToolsCommand(session_id=MockSessionID("TEST_SESSION"))
            result = await message_bridge._handle_list_tools_command(command)
            
            assert result.success
            assert "tools" in result.data
            assert len(result.data["tools"]) == 1
    
    @pytest.mark.asyncio
    async def test_execute_tool_high_level(self, message_bridge):
        """Test high-level tool execution."""
        result = await message_bridge.execute_tool(
            "test_server",
            "test_tool",
            {"arg1": "value1"}
        )
        
        assert result["success"]
        assert "result" in result
    
    @pytest.mark.asyncio
    async def test_register_all_tools(self, message_bridge):
        """Test registering all available tools."""
        with patch.object(message_bridge.tool_adapter, 'list_available_tools') as mock_list:
            mock_list.return_value = [
                {
                    "mcp_name": "test_server",
                    "tool_name": "test_tool",
                    "input_schema": {"type": "object"}
                }
            ]
            
            await message_bridge.register_all_tools()
            
            # Check that events were published
            assert len(message_bridge.message_bus.events) > 0
    
    def test_event_handler_management(self, message_bridge):
        """Test event handler management."""
        async def test_handler(event):
            pass
        
        # Add handler
        message_bridge.add_event_handler(MCPToolRegisteredEvent, test_handler)
        assert MCPToolRegisteredEvent in message_bridge.event_handlers
        
        # Remove handler
        message_bridge.remove_event_handler(MCPToolRegisteredEvent, test_handler)
        assert MCPToolRegisteredEvent not in message_bridge.event_handlers
    
    @pytest.mark.asyncio
    async def test_emit_event(self, message_bridge):
        """Test event emission."""
        event = MCPToolRegisteredEvent(
            mcp_name="test_server",
            tool_name="test_tool",
            session_id=MockSessionID("TEST_SESSION")
        )
        
        await message_bridge.emit_event(event)
        
        # Check that event was published to message bus
        assert len(message_bridge.message_bus.events) > 0
        assert message_bridge.message_bus.events[0] == event
    
    def test_execution_tracking(self, message_bridge):
        """Test execution tracking."""
        execution_id = "test_execution"
        execution_data = {
            "mcp_name": "test_server",
            "tool_name": "test_tool",
            "start_time": "2024-01-01T00:00:00",
            "status": "running"
        }
        
        message_bridge.active_executions[execution_id] = execution_data
        
        # Test getting execution status
        status = message_bridge.get_execution_status(execution_id)
        assert status == execution_data
        
        # Test getting all active executions
        active = message_bridge.get_active_executions()
        assert execution_id in active
    
    @pytest.mark.asyncio
    async def test_cleanup(self, message_bridge):
        """Test bridge cleanup."""
        # Add some active executions
        message_bridge.active_executions["test1"] = {"status": "running"}
        message_bridge.active_executions["test2"] = {"status": "running"}
        
        # Add event handlers
        async def test_handler(event):
            pass
        message_bridge.add_event_handler(MCPToolRegisteredEvent, test_handler)
        
        await message_bridge.cleanup()
        
        # Check that executions were cancelled
        for execution in message_bridge.active_executions.values():
            assert execution["status"] == "cancelled"
        
        # Check that event handlers were cleared
        assert len(message_bridge.event_handlers) == 0


class TestMCPEvents:
    """Test cases for MCP event classes."""
    
    def test_mcp_tool_registered_event(self):
        """Test MCPToolRegisteredEvent creation."""
        event = MCPToolRegisteredEvent(
            mcp_name="test_server",
            tool_name="test_tool",
            tool_schema={"type": "object"},
            session_id=MockSessionID("TEST_SESSION")
        )
        
        assert event.mcp_name == "test_server"
        assert event.tool_name == "test_tool"
        assert event.tool_schema == {"type": "object"}
        assert event.registration_time is not None
    
    def test_mcp_tool_execution_started_event(self):
        """Test MCPToolExecutionStartedEvent creation."""
        event = MCPToolExecutionStartedEvent(
            mcp_name="test_server",
            tool_name="test_tool",
            tool_arguments={"arg1": "value1"},
            session_id=MockSessionID("TEST_SESSION")
        )
        
        assert event.mcp_name == "test_server"
        assert event.tool_name == "test_tool"
        assert event.tool_arguments == {"arg1": "value1"}
        assert event.execution_id is not None
        assert event.start_time is not None
    
    def test_mcp_tool_execution_completed_event(self):
        """Test MCPToolExecutionCompletedEvent creation."""
        event = MCPToolExecutionCompletedEvent(
            mcp_name="test_server",
            tool_name="test_tool",
            execution_id="test_execution",
            tool_result="test result",
            success=True,
            session_id=MockSessionID("TEST_SESSION")
        )
        
        assert event.mcp_name == "test_server"
        assert event.tool_name == "test_tool"
        assert event.execution_id == "test_execution"
        assert event.tool_result == "test result"
        assert event.success
        assert event.end_time is not None


class TestMCPCommands:
    """Test cases for MCP command classes."""
    
    def test_execute_mcp_tool_command(self):
        """Test ExecuteMCPToolCommand creation."""
        command = ExecuteMCPToolCommand(
            mcp_name="test_server",
            tool_name="test_tool",
            tool_arguments={"arg1": "value1"},
            session_id=MockSessionID("TEST_SESSION")
        )
        
        assert command.mcp_name == "test_server"
        assert command.tool_name == "test_tool"
        assert command.tool_arguments == {"arg1": "value1"}
        assert command.execution_id is not None
    
    def test_register_mcp_tool_command(self):
        """Test RegisterMCPToolCommand creation."""
        command = RegisterMCPToolCommand(
            mcp_name="test_server",
            tool_name="test_tool",
            tool_schema={"type": "object"},
            session_id=MockSessionID("TEST_SESSION")
        )
        
        assert command.mcp_name == "test_server"
        assert command.tool_name == "test_tool"
        assert command.tool_schema == {"type": "object"}
    
    def test_list_mcp_tools_command(self):
        """Test ListMCPToolsCommand creation."""
        command = ListMCPToolsCommand(session_id=MockSessionID("TEST_SESSION"))
        
        assert command.mcp_name == ""
        assert command.tool_name == ""


class TestMCPEventHandlerRegistry:
    """Test cases for MCPEventHandlerRegistry."""
    
    @pytest.fixture
    def registry(self):
        """Create an event handler registry."""
        return MCPEventHandlerRegistry()
    
    def test_registry_initialization(self, registry):
        """Test registry initialization."""
        assert registry.handlers == {}
        assert registry.handler_stats == {}
        assert registry.error_handlers == []
    
    def test_register_handler(self, registry):
        """Test handler registration."""
        async def test_handler(event):
            pass
        
        registry.register_handler("TestEvent", test_handler)
        
        assert "TestEvent" in registry.handlers
        assert test_handler in registry.handlers["TestEvent"]
        assert "TestEvent" in registry.handler_stats
    
    def test_unregister_handler(self, registry):
        """Test handler unregistration."""
        async def test_handler(event):
            pass
        
        registry.register_handler("TestEvent", test_handler)
        registry.unregister_handler("TestEvent", test_handler)
        
        assert "TestEvent" not in registry.handlers
        assert "TestEvent" not in registry.handler_stats
    
    def test_add_error_handler(self, registry):
        """Test error handler addition."""
        def error_handler(exception, event):
            pass
        
        registry.add_error_handler(error_handler)
        assert error_handler in registry.error_handlers
    
    @pytest.mark.asyncio
    async def test_handle_event_success(self, registry):
        """Test successful event handling."""
        handled_events = []
        
        async def test_handler(event):
            handled_events.append(event)
        
        registry.register_handler("TestEvent", test_handler)
        
        # Create a mock event
        event = MagicMock()
        event.__class__.__name__ = "TestEvent"
        
        await registry.handle_event(event)
        
        assert len(handled_events) == 1
        assert handled_events[0] == event
        assert registry.handler_stats["TestEvent"]["successful_events"] == 1
    
    @pytest.mark.asyncio
    async def test_handle_event_failure(self, registry):
        """Test event handling with failures."""
        error_calls = []
        
        async def failing_handler(event):
            raise Exception("Handler failed")
        
        def error_handler(exception, event):
            error_calls.append((exception, event))
        
        registry.register_handler("TestEvent", failing_handler)
        registry.add_error_handler(error_handler)
        
        # Create a mock event
        event = MagicMock()
        event.__class__.__name__ = "TestEvent"
        
        await registry.handle_event(event)
        
        assert len(error_calls) == 1
        assert registry.handler_stats["TestEvent"]["failed_events"] == 1
    
    def test_get_stats(self, registry):
        """Test getting registry statistics."""
        async def test_handler(event):
            pass
        
        registry.register_handler("TestEvent", test_handler)
        
        stats = registry.get_stats()
        
        assert "handler_stats" in stats
        assert "total_handlers" in stats
        assert "event_types" in stats
        assert stats["total_handlers"] == 1
        assert "TestEvent" in stats["event_types"]


class TestMCPToolExecutionTracker:
    """Test cases for MCPToolExecutionTracker."""
    
    @pytest.fixture
    def tracker(self):
        """Create an execution tracker."""
        return MCPToolExecutionTracker(cleanup_interval_minutes=1)
    
    def test_tracker_initialization(self, tracker):
        """Test tracker initialization."""
        assert tracker.active_executions == {}
        assert tracker.completed_executions == []
        assert tracker.execution_metrics["total_executions"] == 0
    
    @pytest.mark.asyncio
    async def test_start_execution(self, tracker):
        """Test starting execution tracking."""
        event = MCPToolExecutionStartedEvent(
            mcp_name="test_server",
            tool_name="test_tool",
            execution_id="test_execution",
            tool_arguments={"arg1": "value1"},
            session_id=MockSessionID("TEST_SESSION")
        )
        
        await tracker.start_execution(event)
        
        assert "test_execution" in tracker.active_executions
        execution_info = tracker.active_executions["test_execution"]
        assert execution_info["mcp_name"] == "test_server"
        assert execution_info["tool_name"] == "test_tool"
        assert execution_info["status"] == "running"
    
    @pytest.mark.asyncio
    async def test_complete_execution(self, tracker):
        """Test completing execution tracking."""
        # Start execution first
        start_event = MCPToolExecutionStartedEvent(
            mcp_name="test_server",
            tool_name="test_tool",
            execution_id="test_execution",
            tool_arguments={"arg1": "value1"},
            session_id=MockSessionID("TEST_SESSION")
        )
        await tracker.start_execution(start_event)
        
        # Complete execution
        complete_event = MCPToolExecutionCompletedEvent(
            mcp_name="test_server",
            tool_name="test_tool",
            execution_id="test_execution",
            tool_result="test result",
            success=True,
            session_id=MockSessionID("TEST_SESSION")
        )
        await tracker.complete_execution(complete_event)
        
        # Check that execution was moved to completed
        assert "test_execution" not in tracker.active_executions
        assert len(tracker.completed_executions) == 1
        
        completed = tracker.completed_executions[0]
        assert completed["execution_id"] == "test_execution"
        assert completed["success"]
        assert completed["result"] == "test result"
        
        # Check metrics were updated
        assert tracker.execution_metrics["total_executions"] == 1
        assert tracker.execution_metrics["successful_executions"] == 1
    
    def test_get_execution_status(self, tracker):
        """Test getting execution status."""
        # Add active execution
        execution_info = {
            "execution_id": "test_execution",
            "mcp_name": "test_server",
            "tool_name": "test_tool",
            "status": "running"
        }
        tracker.active_executions["test_execution"] = execution_info
        
        status = tracker.get_execution_status("test_execution")
        assert status == execution_info
        
        # Test non-existent execution
        status = tracker.get_execution_status("non_existent")
        assert status is None
    
    def test_get_metrics(self, tracker):
        """Test getting execution metrics."""
        metrics = tracker.get_metrics()
        
        assert "total_executions" in metrics
        assert "successful_executions" in metrics
        assert "failed_executions" in metrics
        assert "avg_execution_time_ms" in metrics
        assert "active_executions" in metrics
        assert "completed_executions" in metrics
    
    def test_get_execution_history(self, tracker):
        """Test getting execution history with filters."""
        # Add completed executions
        tracker.completed_executions = [
            {
                "execution_id": "exec1",
                "tool_name": "tool1",
                "mcp_name": "server1",
                "end_time": "2024-01-01T00:00:00"
            },
            {
                "execution_id": "exec2",
                "tool_name": "tool2",
                "mcp_name": "server1",
                "end_time": "2024-01-01T01:00:00"
            },
            {
                "execution_id": "exec3",
                "tool_name": "tool1",
                "mcp_name": "server2",
                "end_time": "2024-01-01T02:00:00"
            }
        ]
        
        # Test no filters
        history = tracker.get_execution_history()
        assert len(history) == 3
        
        # Test tool name filter
        history = tracker.get_execution_history(tool_name="tool1")
        assert len(history) == 2
        
        # Test MCP name filter
        history = tracker.get_execution_history(mcp_name="server1")
        assert len(history) == 2
        
        # Test limit
        history = tracker.get_execution_history(limit=1)
        assert len(history) == 1
    
    @pytest.mark.asyncio
    async def test_cleanup(self, tracker):
        """Test tracker cleanup."""
        await tracker.cleanup()
        assert tracker._cleanup_task.cancelled()


class TestMCPEventHandlers:
    """Test cases for MCPEventHandlers."""
    
    @pytest.fixture
    def handlers(self):
        """Create event handlers."""
        return MCPEventHandlers()
    
    @pytest.mark.asyncio
    async def test_handle_tool_registered(self, handlers):
        """Test tool registration event handling."""
        event = MCPToolRegisteredEvent(
            mcp_name="test_server",
            tool_name="test_tool",
            tool_schema={"type": "object"},
            session_id=MockSessionID("TEST_SESSION")
        )
        
        await handlers.handle_tool_registered(event)
        
        tools = handlers.get_registered_tools()
        assert "test_server:test_tool" in tools
        assert tools["test_server:test_tool"]["mcp_name"] == "test_server"
        assert tools["test_server:test_tool"]["tool_name"] == "test_tool"
    
    @pytest.mark.asyncio
    async def test_handle_execution_started(self, handlers):
        """Test execution started event handling."""
        event = MCPToolExecutionStartedEvent(
            mcp_name="test_server",
            tool_name="test_tool",
            execution_id="test_execution",
            tool_arguments={"arg1": "value1"},
            session_id=MockSessionID("TEST_SESSION")
        )
        
        await handlers.handle_execution_started(event)
        
        # Check that tracker was updated
        status = handlers.tracker.get_execution_status("test_execution")
        assert status is not None
        assert status["status"] == "running"
    
    @pytest.mark.asyncio
    async def test_handle_execution_completed(self, handlers):
        """Test execution completed event handling."""
        # Start execution first
        start_event = MCPToolExecutionStartedEvent(
            mcp_name="test_server",
            tool_name="test_tool",
            execution_id="test_execution",
            tool_arguments={"arg1": "value1"},
            session_id=MockSessionID("TEST_SESSION")
        )
        await handlers.handle_execution_started(start_event)
        
        # Complete execution
        complete_event = MCPToolExecutionCompletedEvent(
            mcp_name="test_server",
            tool_name="test_tool",
            execution_id="test_execution",
            tool_result="test result",
            success=True,
            session_id=MockSessionID("TEST_SESSION")
        )
        await handlers.handle_execution_completed(complete_event)
        
        # Check that execution was completed
        metrics = handlers.get_execution_metrics()
        assert metrics["total_executions"] == 1
        assert metrics["successful_executions"] == 1
    
    @pytest.mark.asyncio
    async def test_handle_server_connection(self, handlers):
        """Test server connection event handling."""
        # Register a tool first
        register_event = MCPToolRegisteredEvent(
            mcp_name="test_server",
            tool_name="test_tool",
            session_id=MockSessionID("TEST_SESSION")
        )
        await handlers.handle_tool_registered(register_event)
        
        # Disconnect server
        disconnect_event = MCPServerConnectionEvent(
            mcp_name="test_server",
            connection_status="disconnected",
            session_id=MockSessionID("TEST_SESSION")
        )
        await handlers.handle_server_connection(disconnect_event)
        
        # Check that tool was removed
        tools = handlers.get_registered_tools()
        assert "test_server:test_tool" not in tools
    
    @pytest.mark.asyncio
    async def test_cleanup(self, handlers):
        """Test handlers cleanup."""
        await handlers.cleanup()
        # Cleanup should complete without errors


class TestUtilityFunctions:
    """Test cases for utility functions."""
    
    def test_create_default_event_handlers(self):
        """Test creating default event handlers."""
        from any_mcp.integration.event_handlers import create_default_event_handlers
        
        handlers = create_default_event_handlers()
        assert isinstance(handlers, MCPEventHandlers)
    
    def test_setup_event_registry_with_defaults(self):
        """Test setting up event registry with defaults."""
        registry = setup_event_registry_with_defaults()
        
        assert isinstance(registry, MCPEventHandlerRegistry)
        assert "MCPToolRegisteredEvent" in registry.handlers
        assert "MCPToolExecutionStartedEvent" in registry.handlers
        assert "MCPToolExecutionCompletedEvent" in registry.handlers
        assert "MCPServerConnectionEvent" in registry.handlers
    
    def test_create_logging_error_handler(self):
        """Test creating logging error handler."""
        from any_mcp.integration.event_handlers import create_logging_error_handler
        
        error_handler = create_logging_error_handler()
        assert callable(error_handler)
        
        # Test calling error handler
        event = MagicMock()
        event.__class__.__name__ = "TestEvent"
        event.mcp_name = "test_server"
        event.tool_name = "test_tool"
        event.execution_id = "test_execution"
        
        # Should not raise an exception
        error_handler(Exception("test error"), event)


if __name__ == "__main__":
    pytest.main([__file__])
