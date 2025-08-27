"""
Integration tests for MCP integration with llmgine.

These tests verify that the MCP integration works correctly with the
existing llmgine architecture.
"""

import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from llmgine.llm.context.memory import SimpleChatHistory
from llmgine.llm.tools.toolCall import ToolCall
from llmgine.llm.tools.enhanced_tool_manager import (
    EnhancedToolManager,
    MCPServerConfig,
    create_enhanced_tool_manager_with_servers
)

from any_mcp.managers.manager import MCPManager
from any_mcp.core.client import MCPClient


class TestEnhancedToolManager:
    """Test the enhanced tool manager."""
    
    @pytest.fixture
    def chat_history(self):
        """Create a chat history for testing."""
        history = SimpleChatHistory()
        history.set_system_prompt("Test system prompt")
        return history
    
    def test_enhanced_tool_manager_initialization(self, chat_history):
        """Test that enhanced tool manager initializes correctly."""
        manager = EnhancedToolManager(chat_history)
        
        assert manager.chat_history == chat_history
        assert manager.mcp_manager is None
        assert manager.tool_adapter is None
        assert not manager._mcp_initialized
        assert manager.tools == {}
        assert manager.tool_schemas == []
    
    def test_local_tool_registration(self, chat_history):
        """Test that local tools can be registered."""
        manager = EnhancedToolManager(chat_history)
        
        def test_tool(x: int, y: int) -> int:
            """Test tool that adds two numbers."""
            return x + y
        
        manager.register_tool(test_tool)
        
        assert "test_tool" in manager.tools
        assert len(manager.tool_schemas) == 1
        assert manager.tool_schemas[0]["function"]["name"] == "test_tool"
    
    @pytest.mark.asyncio
    async def test_mcp_initialization(self, chat_history):
        """Test MCP system initialization."""
        manager = EnhancedToolManager(chat_history)
        
        with patch('any_mcp.managers.manager.MCPManager') as mock_mcp_manager:
            mock_manager = AsyncMock()
            mock_mcp_manager.return_value = mock_manager
            
            success = await manager.initialize_mcp()
            
            assert success
            assert manager._mcp_initialized
            assert manager.mcp_manager is not None
            assert manager.tool_adapter is not None
    
    @pytest.mark.asyncio
    async def test_local_tool_execution(self, chat_history):
        """Test execution of local tools."""
        manager = EnhancedToolManager(chat_history)
        
        def add_numbers(a: int, b: int) -> int:
            """Add two numbers."""
            return a + b
        
        manager.register_tool(add_numbers)
        
        tool_call = ToolCall(
            id="test_call",
            name="add_numbers",
            arguments='{"a": 5, "b": 3}'
        )
        
        result = await manager.execute_tool_call(tool_call)
        assert result == 8
    
    @pytest.mark.asyncio
    async def test_mcp_server_addition(self, chat_history):
        """Test adding MCP servers."""
        manager = EnhancedToolManager(chat_history)
        
        with patch('any_mcp.managers.manager.MCPManager') as mock_mcp_manager:
            mock_manager = AsyncMock()
            mock_manager.start_mcp = AsyncMock(return_value=True)
            mock_mcp_manager.return_value = mock_manager
            
            # Initialize MCP
            await manager.initialize_mcp()
            
            # Mock tool adapter
            manager.tool_adapter.get_all_openai_schemas = AsyncMock(return_value=[])
            manager.tool_adapter.list_available_tools = AsyncMock(return_value=[])
            
            # Add server
            success = await manager.add_mcp_server(
                "test_server",
                "python",
                ["test_server.py"],
                {}
            )
            
            assert success
            mock_manager.start_mcp.assert_called_once_with(
                "test_server",
                "python",
                ["test_server.py"],
                {}
            )
    
    @pytest.mark.asyncio
    async def test_tool_listing(self, chat_history):
        """Test listing all tools."""
        manager = EnhancedToolManager(chat_history)
        
        # Add local tool
        def local_tool():
            """Local test tool."""
            return "local result"
        
        manager.register_tool(local_tool)
        
        # Mock MCP initialization
        with patch('any_mcp.managers.manager.MCPManager') as mock_mcp_manager:
            mock_manager = AsyncMock()
            mock_manager.active_clients = {"test_server": AsyncMock()}
            mock_mcp_manager.return_value = mock_manager
            
            await manager.initialize_mcp()
            manager._mcp_tools_cache = [
                {"mcp_name": "test_server", "tool_name": "test_tool"}
            ]
            
            tools_info = await manager.list_all_tools()
            
            assert "local_tool" in tools_info["local_tools"]
            assert len(tools_info["mcp_tools"]) == 1
            assert "test_server" in tools_info["mcp_servers"]
    
    @pytest.mark.asyncio
    async def test_cleanup(self, chat_history):
        """Test cleanup of resources."""
        manager = EnhancedToolManager(chat_history)
        
        with patch('any_mcp.managers.manager.MCPManager') as mock_mcp_manager:
            mock_manager = AsyncMock()
            mock_mcp_manager.return_value = mock_manager
            
            await manager.initialize_mcp()
            await manager.cleanup()
            
            mock_manager.cleanup.assert_called_once()


class TestMCPServerConfig:
    """Test MCP server configuration."""
    
    def test_server_config_creation(self):
        """Test creating server config."""
        config = MCPServerConfig(
            name="test_server",
            command="python",
            args=["server.py"],
            env={"KEY": "value"}
        )
        
        assert config.name == "test_server"
        assert config.command == "python"
        assert config.args == ["server.py"]
        assert config.env == {"KEY": "value"}


class TestCreateEnhancedToolManager:
    """Test the factory function for creating enhanced tool managers."""
    
    @pytest.mark.asyncio
    async def test_create_with_servers(self):
        """Test creating enhanced tool manager with MCP servers."""
        chat_history = SimpleChatHistory()
        
        servers = [
            MCPServerConfig("server1", "python", ["server1.py"]),
            MCPServerConfig("server2", "python", ["server2.py"])
        ]
        
        with patch('any_mcp.managers.manager.MCPManager') as mock_mcp_manager:
            mock_manager = AsyncMock()
            mock_manager.start_mcp = AsyncMock(return_value=True)
            mock_mcp_manager.return_value = mock_manager
            
            # Mock tool adapter methods
            with patch('any_mcp.integration.tool_adapter.LLMgineToolAdapter') as mock_adapter:
                mock_adapter_instance = AsyncMock()
                mock_adapter_instance.get_all_openai_schemas = AsyncMock(return_value=[])
                mock_adapter_instance.list_available_tools = AsyncMock(return_value=[])
                mock_adapter.return_value = mock_adapter_instance
                
                manager = await create_enhanced_tool_manager_with_servers(
                    chat_history,
                    servers
                )
                
                assert isinstance(manager, EnhancedToolManager)
                assert manager._mcp_initialized
                
                # Verify servers were added
                assert mock_manager.start_mcp.call_count == 2


class TestMCPManager:
    """Test the MCP manager component."""
    
    @pytest.mark.asyncio
    async def test_mcp_manager_initialization(self):
        """Test MCP manager initialization."""
        manager = MCPManager()
        
        assert manager.active_clients == {}
        assert manager._server_configs == {}
    
    @pytest.mark.asyncio
    async def test_start_mcp_server(self):
        """Test starting an MCP server."""
        manager = MCPManager()
        
        with patch('any_mcp.core.client.MCPClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client.connect = AsyncMock(return_value=True)
            mock_client_class.return_value = mock_client
            
            success = await manager.start_mcp("test_server", "python", ["test.py"])
            
            assert success
            assert "test_server" in manager.active_clients
            assert "test_server" in manager._server_configs
    
    @pytest.mark.asyncio
    async def test_stop_mcp_server(self):
        """Test stopping an MCP server."""
        manager = MCPManager()
        
        # Add a mock client
        mock_client = AsyncMock()
        manager.active_clients["test_server"] = mock_client
        manager._server_configs["test_server"] = {}
        
        success = await manager.stop_mcp("test_server")
        
        assert success
        assert "test_server" not in manager.active_clients
        assert "test_server" not in manager._server_configs
        mock_client.disconnect.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_list_all_tools(self):
        """Test listing tools from all servers."""
        manager = MCPManager()
        
        # Mock client with tools
        mock_client = AsyncMock()
        mock_tool = MagicMock()
        mock_tool.name = "test_tool"
        mock_client.list_tools = AsyncMock(return_value=[mock_tool])
        
        manager.active_clients["test_server"] = mock_client
        
        all_tools = await manager.list_all_tools()
        
        assert "test_server" in all_tools
        assert len(all_tools["test_server"]) == 1
        assert all_tools["test_server"][0].name == "test_tool"
    
    @pytest.mark.asyncio
    async def test_call_mcp_tool(self):
        """Test calling an MCP tool."""
        manager = MCPManager()
        
        # Mock client
        mock_client = AsyncMock()
        mock_result = MagicMock()
        mock_client.call_tool = AsyncMock(return_value=mock_result)
        
        manager.active_clients["test_server"] = mock_client
        
        result = await manager.call_mcp("test_server", "test_tool", {"arg": "value"})
        
        assert result == mock_result
        mock_client.call_tool.assert_called_once_with("test_tool", {"arg": "value"})
    
    @pytest.mark.asyncio
    async def test_find_tool(self):
        """Test finding a tool across servers."""
        manager = MCPManager()
        
        # Mock client with tool
        mock_client = AsyncMock()
        mock_tool = MagicMock()
        mock_tool.name = "target_tool"
        mock_client.get_tool = AsyncMock(return_value=mock_tool)
        
        manager.active_clients["test_server"] = mock_client
        
        result = await manager.find_tool("target_tool")
        
        assert result is not None
        assert result[0] == "test_server"
        assert result[1] == mock_tool
    
    @pytest.mark.asyncio
    async def test_health_check(self):
        """Test health check of servers."""
        manager = MCPManager()
        
        # Mock healthy client
        healthy_client = AsyncMock()
        healthy_client.list_tools = AsyncMock(return_value=[])
        
        # Mock unhealthy client
        unhealthy_client = AsyncMock()
        unhealthy_client.list_tools = AsyncMock(side_effect=Exception("Connection failed"))
        
        manager.active_clients["healthy_server"] = healthy_client
        manager.active_clients["unhealthy_server"] = unhealthy_client
        
        health_status = await manager.health_check()
        
        assert health_status["healthy_server"] is True
        assert health_status["unhealthy_server"] is False
    
    @pytest.mark.asyncio
    async def test_cleanup(self):
        """Test cleanup of manager."""
        manager = MCPManager()
        
        # Add mock clients
        mock_client1 = AsyncMock()
        mock_client2 = AsyncMock()
        
        manager.active_clients["server1"] = mock_client1
        manager.active_clients["server2"] = mock_client2
        manager._server_configs["server1"] = {}
        manager._server_configs["server2"] = {}
        
        await manager.cleanup()
        
        assert len(manager.active_clients) == 0
        assert len(manager._server_configs) == 0
        mock_client1.disconnect.assert_called_once()
        mock_client2.disconnect.assert_called_once()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

