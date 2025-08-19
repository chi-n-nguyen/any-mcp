"""
Integration Tests for llmgine-MCP Integration

This module provides comprehensive integration tests for the MCP integration
with llmgine, including ToolManager replacement, MessageBus integration,
and end-to-end tool execution workflows.
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Dict, Any, List

# llmgine imports
from llmgine.bus.bus import MessageBus
from llmgine.llm import SessionID
from llmgine.llm.context.memory import SimpleChatHistory
from llmgine.llm.tools.toolCall import ToolCall

# MCP integration imports
from llmgine.llm.tools.mcp_tool_manager import (
    MCPToolManager,
    MCPServerConfig,
    ToolManagerMigrationHelper,
    create_mcp_tool_manager,
    create_default_mcp_servers
)
from llmgine.llm.tools.mcp_bridge_integration import (
    LLMgineMCPBridge,
    create_llmgine_mcp_integration,
    ExecuteMCPToolLLMgineCommand,
    RegisterMCPServerCommand,
    MCPToolExecutionLLMgineEvent,
    MCPToolRegisteredLLMgineEvent
)
from llmgine.llm.tools.mcp_registry import (
    MCPServerRegistry,
    MCPServerDefinition,
    create_default_registry
)

# Original ToolManager for comparison
from llmgine.llm.tools.tool_manager import ToolManager as OriginalToolManager

# Mock any_mcp components
from any_mcp.managers.manager import MCPManager


# ==================== Test Fixtures ====================

@pytest.fixture
async def llmgine_bus():
    """Create and start a llmgine MessageBus."""
    bus = MessageBus()
    await bus.start()
    yield bus
    await bus.stop()


@pytest.fixture
def chat_history():
    """Create a SimpleChatHistory instance."""
    history = SimpleChatHistory()
    history.set_system_prompt("Test system prompt")
    return history


@pytest.fixture
def session_id():
    """Create a test session ID."""
    return SessionID("test_integration_session")


@pytest.fixture
async def mock_mcp_manager():
    """Create a mock MCP manager."""
    manager = AsyncMock(spec=MCPManager)
    manager.active_clients = {"test_server": AsyncMock()}
    manager.call_mcp = AsyncMock(return_value=AsyncMock(
        content=[AsyncMock(text="test result")],
        isError=False
    ))
    manager.start_mcp = AsyncMock()
    manager.cleanup = AsyncMock()
    return manager


@pytest.fixture
def sample_mcp_servers():
    """Create sample MCP server configurations."""
    return [
        MCPServerConfig(
            name="calculator",
            command="python",
            args=["mcps/demo_calculator.py"],
            env={},
            auto_start=True
        ),
        MCPServerConfig(
            name="test_server",
            command="python",
            args=["test_server.py"],
            env={},
            auto_start=True
        )
    ]


def sample_tool_function(x: int, y: int) -> int:
    """Sample tool function for testing."""
    return x + y


# ==================== MCPToolManager Tests ====================

class TestMCPToolManager:
    """Test cases for MCPToolManager integration."""
    
    @pytest.mark.asyncio
    async def test_initialization(self, chat_history, session_id):
        """Test MCPToolManager initialization."""
        manager = MCPToolManager(chat_history, str(session_id))
        
        assert manager.chat_history == chat_history
        assert manager.session_id.value == str(session_id)
        assert manager.local_tools == {}
        assert manager.local_tool_schemas == []
        assert not manager._initialized
        
        # Test initialization
        with patch('llmgine.llm.tools.mcp_tool_manager.MCPManager') as mock_mcp_manager:
            mock_mcp_manager.return_value = AsyncMock()
            await manager.initialize()
            
            assert manager._initialized
            assert manager.mcp_manager is not None
            assert manager.message_bridge is not None
    
    def test_local_tool_registration(self, chat_history, session_id):
        """Test registration of local tools (backwards compatibility)."""
        manager = MCPToolManager(chat_history, str(session_id))
        
        # Register a local tool
        manager.register_tool(sample_tool_function)
        
        assert "sample_tool_function" in manager.local_tools
        assert len(manager.local_tool_schemas) == 1
        assert manager.local_tool_schemas[0]["function"]["name"] == "sample_tool_function"
    
    @pytest.mark.asyncio
    async def test_tool_execution_local(self, chat_history, session_id):
        """Test execution of local tools."""
        manager = MCPToolManager(chat_history, str(session_id))
        manager.register_tool(sample_tool_function)
        
        # Create a tool call
        tool_call = ToolCall(
            id="test_call",
            name="sample_tool_function",
            arguments='{"x": 5, "y": 3}'
        )
        
        # Execute the tool
        result = await manager.execute_tool_call(tool_call)
        
        assert result == 8
    
    @pytest.mark.asyncio
    async def test_mcp_server_registration(self, chat_history, session_id, sample_mcp_servers):
        """Test MCP server registration."""
        manager = MCPToolManager(chat_history, str(session_id))
        
        with patch('llmgine.llm.tools.mcp_tool_manager.MCPManager') as mock_mcp_manager_class:
            mock_manager = AsyncMock()
            mock_mcp_manager_class.return_value = mock_manager
            
            await manager.initialize()
            
            # Register servers
            results = await manager.register_mcp_servers(sample_mcp_servers)
            
            assert len(results) == 2
            assert results["calculator"] == True
            assert results["test_server"] == True
            
            # Verify MCP manager was called
            assert mock_manager.start_mcp.call_count == 2
    
    @pytest.mark.asyncio
    async def test_tool_schema_generation(self, chat_history, session_id):
        """Test tool schema generation."""
        manager = MCPToolManager(chat_history, str(session_id))
        
        # Register local tool
        manager.register_tool(sample_tool_function)
        
        # Check schema generation
        schemas = manager.tool_schemas
        assert len(schemas) == 1
        
        schema = schemas[0]
        assert schema["type"] == "function"
        assert schema["function"]["name"] == "sample_tool_function"
        assert "parameters" in schema["function"]
    
    @pytest.mark.asyncio
    async def test_cleanup(self, chat_history, session_id):
        """Test MCPToolManager cleanup."""
        manager = MCPToolManager(chat_history, str(session_id))
        
        with patch('llmgine.llm.tools.mcp_tool_manager.MCPManager') as mock_mcp_manager_class:
            mock_manager = AsyncMock()
            mock_mcp_manager_class.return_value = mock_manager
            
            await manager.initialize()
            await manager.cleanup()
            
            mock_manager.cleanup.assert_called_once()


class TestToolManagerMigration:
    """Test cases for migrating from original ToolManager."""
    
    def test_migration_from_original(self, chat_history):
        """Test migration from original ToolManager to MCPToolManager."""
        # Create original manager with tools
        original_manager = OriginalToolManager(chat_history)
        original_manager.register_tool(sample_tool_function)
        
        # Migrate to MCP manager
        mcp_manager = ToolManagerMigrationHelper.migrate_from_original(original_manager)
        
        assert isinstance(mcp_manager, MCPToolManager)
        assert mcp_manager.chat_history == chat_history
        assert "sample_tool_function" in mcp_manager.local_tools
        assert len(mcp_manager.local_tool_schemas) == 1
    
    def test_hybrid_manager_creation(self, chat_history, sample_mcp_servers):
        """Test creation of hybrid manager with both local and MCP tools."""
        # Create original manager
        original_manager = OriginalToolManager(chat_history)
        original_manager.register_tool(sample_tool_function)
        
        # Create hybrid manager
        hybrid_manager = ToolManagerMigrationHelper.create_hybrid_manager(
            original_manager,
            sample_mcp_servers
        )
        
        assert isinstance(hybrid_manager, MCPToolManager)
        assert "sample_tool_function" in hybrid_manager.local_tools
        assert hasattr(hybrid_manager, '_server_configs')


# ==================== LLMgineMCPBridge Tests ====================

class TestLLMgineMCPBridge:
    """Test cases for LLMgineMCPBridge integration."""
    
    @pytest.mark.asyncio
    async def test_bridge_initialization(self, llmgine_bus, session_id):
        """Test bridge initialization."""
        bridge = LLMgineMCPBridge(llmgine_bus, session_id)
        
        assert bridge.llmgine_bus == llmgine_bus
        assert bridge.session_id == session_id
        assert not bridge._initialized
        
        # Test initialization
        with patch('llmgine.llm.tools.mcp_bridge_integration.MCPManager') as mock_manager:
            mock_manager.return_value = AsyncMock()
            
            success = await bridge.initialize()
            
            assert success
            assert bridge._initialized
            assert bridge.mcp_manager is not None
    
    @pytest.mark.asyncio
    async def test_command_execution(self, llmgine_bus, session_id):
        """Test MCP command execution through bridge."""
        bridge = LLMgineMCPBridge(llmgine_bus, session_id)
        
        with patch('llmgine.llm.tools.mcp_bridge_integration.MCPManager') as mock_manager_class:
            mock_manager = AsyncMock()
            mock_manager_class.return_value = mock_manager
            
            await bridge.initialize()
            
            # Test tool execution command
            result = await bridge.execute_mcp_tool(
                "test_server",
                "test_tool",
                {"arg1": "value1"}
            )
            
            assert "success" in result
            assert "result" in result
    
    @pytest.mark.asyncio
    async def test_server_registration(self, llmgine_bus, session_id):
        """Test MCP server registration through bridge."""
        bridge = LLMgineMCPBridge(llmgine_bus, session_id)
        
        with patch('llmgine.llm.tools.mcp_bridge_integration.MCPManager') as mock_manager_class:
            mock_manager = AsyncMock()
            mock_manager_class.return_value = mock_manager
            
            await bridge.initialize()
            
            # Test server registration
            success = await bridge.register_mcp_server(
                "test_server",
                "python",
                ["test_server.py"],
                {}
            )
            
            assert success
            mock_manager.start_mcp.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_event_translation(self, llmgine_bus, session_id):
        """Test event translation between MCP and llmgine formats."""
        bridge = LLMgineMCPBridge(llmgine_bus, session_id)
        
        # Track published events
        published_events = []
        
        async def capture_event(event):
            published_events.append(event)
        
        # Mock bus publish to capture events
        original_publish = llmgine_bus.publish
        llmgine_bus.publish = capture_event
        
        try:
            with patch('llmgine.llm.tools.mcp_bridge_integration.MCPManager'):
                await bridge.initialize()
                
                # Create and translate an MCP event
                from any_mcp.integration.message_bridge import MCPToolRegisteredEvent
                
                mcp_event = MCPToolRegisteredEvent(
                    mcp_name="test_server",
                    tool_name="test_tool",
                    tool_schema={"type": "object"},
                    session_id=session_id
                )
                
                await bridge._translate_tool_registered(mcp_event)
                
                # Check that llmgine event was published
                assert len(published_events) == 1
                assert isinstance(published_events[0], MCPToolRegisteredLLMgineEvent)
                assert published_events[0].mcp_name == "test_server"
                assert published_events[0].tool_name == "test_tool"
        
        finally:
            llmgine_bus.publish = original_publish
    
    @pytest.mark.asyncio
    async def test_cleanup(self, llmgine_bus, session_id):
        """Test bridge cleanup."""
        bridge = LLMgineMCPBridge(llmgine_bus, session_id)
        
        with patch('llmgine.llm.tools.mcp_bridge_integration.MCPManager') as mock_manager_class:
            mock_manager = AsyncMock()
            mock_manager_class.return_value = mock_manager
            
            await bridge.initialize()
            await bridge.cleanup()
            
            mock_manager.cleanup.assert_called_once()


# ==================== MCPServerRegistry Tests ====================

class TestMCPServerRegistry:
    """Test cases for MCP server registry."""
    
    def test_registry_initialization(self):
        """Test registry initialization."""
        registry = MCPServerRegistry()
        
        assert registry.server_definitions == {}
        assert registry.discovered_tools == {}
        assert registry.server_health == {}
    
    def test_server_registration(self):
        """Test server definition registration."""
        registry = MCPServerRegistry()
        
        definition = MCPServerDefinition(
            name="test_server",
            command="python",
            args=["test.py"],
            description="Test server"
        )
        
        success = registry.register_server(definition)
        
        assert success
        assert "test_server" in registry.server_definitions
        assert "test_server" in registry.server_health
    
    def test_server_listing(self):
        """Test server listing with filters."""
        registry = MCPServerRegistry()
        
        # Register servers with different tags
        server1 = MCPServerDefinition(
            name="calc",
            command="python",
            args=["calc.py"],
            tags=["math", "utility"]
        )
        
        server2 = MCPServerDefinition(
            name="web",
            command="python", 
            args=["web.py"],
            tags=["web", "search"]
        )
        
        registry.register_server(server1)
        registry.register_server(server2)
        
        # Test listing all
        all_servers = registry.list_servers()
        assert len(all_servers) == 2
        
        # Test filtering by tags
        math_servers = registry.list_servers(tags=["math"])
        assert len(math_servers) == 1
        assert math_servers[0].name == "calc"
    
    def test_configuration_loading(self, tmp_path):
        """Test loading configuration from file."""
        registry = MCPServerRegistry()
        
        # Create test config
        config = {
            "mcp_servers": [
                {
                    "name": "test_server",
                    "command": "python",
                    "args": ["test.py"],
                    "description": "Test server",
                    "tags": ["test"]
                }
            ]
        }
        
        # Write config file
        config_file = tmp_path / "test_config.json"
        import json
        with open(config_file, 'w') as f:
            json.dump(config, f)
        
        # Load configuration
        loaded_count = registry.load_from_file(config_file)
        
        assert loaded_count == 1
        assert "test_server" in registry.server_definitions
    
    def test_registry_stats(self):
        """Test registry statistics."""
        registry = create_default_registry()
        
        stats = registry.get_registry_stats()
        
        assert "total_servers" in stats
        assert "total_tools" in stats
        assert "servers_by_status" in stats
        assert stats["total_servers"] >= 2  # Default servers


# ==================== Integration Tests ====================

class TestEndToEndIntegration:
    """End-to-end integration tests."""
    
    @pytest.mark.asyncio
    async def test_complete_integration_workflow(self, llmgine_bus, chat_history, session_id):
        """Test complete integration workflow from setup to execution."""
        # Step 1: Create MCP tool manager
        tool_manager = MCPToolManager(chat_history, str(session_id))
        
        # Step 2: Register local tool
        tool_manager.register_tool(sample_tool_function)
        
        # Step 3: Initialize with mock MCP system
        with patch('llmgine.llm.tools.mcp_tool_manager.MCPManager') as mock_manager_class:
            mock_manager = AsyncMock()
            mock_manager_class.return_value = mock_manager
            
            await tool_manager.initialize()
            
            # Step 4: Execute local tool
            tool_call = ToolCall(
                id="test_call",
                name="sample_tool_function",
                arguments='{"x": 10, "y": 20}'
            )
            
            result = await tool_manager.execute_tool_call(tool_call)
            assert result == 30
            
            # Step 5: Test tool schemas
            schemas = tool_manager.tool_schemas
            assert len(schemas) >= 1
            
            # Step 6: Cleanup
            await tool_manager.cleanup()
    
    @pytest.mark.asyncio
    async def test_bridge_and_manager_integration(self, llmgine_bus, session_id):
        """Test integration between bridge and tool manager."""
        # Create bridge
        bridge = LLMgineMCPBridge(llmgine_bus, session_id)
        
        # Create tool manager
        tool_manager = MCPToolManager(None, str(session_id))
        
        with patch('llmgine.llm.tools.mcp_bridge_integration.MCPManager') as mock_bridge_manager:
            with patch('llmgine.llm.tools.mcp_tool_manager.MCPManager') as mock_tool_manager:
                mock_bridge_manager.return_value = AsyncMock()
                mock_tool_manager.return_value = AsyncMock()
                
                # Initialize both
                await bridge.initialize()
                await tool_manager.initialize()
                
                # Test that they can work together
                assert bridge._initialized
                assert tool_manager._initialized
                
                # Cleanup
                await bridge.cleanup()
                await tool_manager.cleanup()
    
    @pytest.mark.asyncio
    async def test_event_flow_integration(self, llmgine_bus, session_id):
        """Test event flow through the integrated system."""
        events_received = []
        
        # Event handler to capture events
        async def event_handler(event):
            events_received.append(event)
        
        # Register event handlers
        llmgine_bus.register_event_handler(
            MCPToolExecutionLLMgineEvent,
            event_handler,
            session_id
        )
        
        llmgine_bus.register_event_handler(
            MCPToolRegisteredLLMgineEvent,
            event_handler,
            session_id
        )
        
        # Create and initialize bridge
        bridge = LLMgineMCPBridge(llmgine_bus, session_id)
        
        with patch('llmgine.llm.tools.mcp_bridge_integration.MCPManager') as mock_manager_class:
            mock_manager = AsyncMock()
            mock_manager_class.return_value = mock_manager
            
            await bridge.initialize()
            
            # Simulate MCP events
            from any_mcp.integration.message_bridge import MCPToolRegisteredEvent
            
            mcp_event = MCPToolRegisteredEvent(
                mcp_name="test_server",
                tool_name="test_tool",
                session_id=session_id
            )
            
            await bridge._translate_tool_registered(mcp_event)
            
            # Wait for event processing
            await asyncio.sleep(0.1)
            
            # Check that events were received
            assert len(events_received) >= 1
            assert any(isinstance(event, MCPToolRegisteredLLMgineEvent) for event in events_received)


# ==================== Performance Tests ====================

class TestPerformanceIntegration:
    """Performance tests for MCP integration."""
    
    @pytest.mark.asyncio
    async def test_tool_execution_performance(self, chat_history, session_id):
        """Test performance of tool execution."""
        import time
        
        tool_manager = MCPToolManager(chat_history, str(session_id))
        tool_manager.register_tool(sample_tool_function)
        
        # Measure execution time
        start_time = time.time()
        
        for i in range(10):
            tool_call = ToolCall(
                id=f"call_{i}",
                name="sample_tool_function",
                arguments=f'{{"x": {i}, "y": {i+1}}}'
            )
            
            result = await tool_manager.execute_tool_call(tool_call)
            assert result == i + (i + 1)
        
        end_time = time.time()
        execution_time = end_time - start_time
        
        # Should complete 10 tool calls in reasonable time
        assert execution_time < 1.0  # Less than 1 second
        
        print(f"Executed 10 tool calls in {execution_time:.3f} seconds")
    
    @pytest.mark.asyncio
    async def test_concurrent_tool_execution(self, chat_history, session_id):
        """Test concurrent tool execution."""
        tool_manager = MCPToolManager(chat_history, str(session_id))
        tool_manager.register_tool(sample_tool_function)
        
        # Create multiple tool calls
        tool_calls = [
            ToolCall(
                id=f"concurrent_call_{i}",
                name="sample_tool_function",
                arguments=f'{{"x": {i}, "y": {i*2}}}'
            )
            for i in range(5)
        ]
        
        # Execute concurrently
        import time
        start_time = time.time()
        
        results = await tool_manager.execute_tool_calls(tool_calls)
        
        end_time = time.time()
        execution_time = end_time - start_time
        
        # Check results
        assert len(results) == 5
        for i, result in enumerate(results):
            expected = i + (i * 2)
            assert result == expected
        
        print(f"Executed 5 concurrent tool calls in {execution_time:.3f} seconds")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

