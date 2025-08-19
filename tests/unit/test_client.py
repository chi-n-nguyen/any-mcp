"""
Unit tests for MCP client functionality
"""
import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from mcp import ClientSession, types
from mcp.types import CallToolResult, TextContent

from any_mcp.core.client import MCPClient


class TestMCPClient:
    """Test cases for MCPClient class."""
    
    @pytest.fixture
    def client(self):
        """Create a fresh MCPClient instance for each test."""
        return MCPClient(
            command="python",
            args=["./test_server.py"],
            env={"TEST_VAR": "test_value"}
        )
    
    @pytest.fixture
    def mock_session(self):
        """Create a mock ClientSession."""
        session = AsyncMock(spec=ClientSession)
        session.initialize = AsyncMock()
        session.list_tools = AsyncMock()
        session.call_tool = AsyncMock()
        session.list_prompts = AsyncMock()
        session.get_prompt = AsyncMock()
        session.read_resource = AsyncMock()
        session.aclose = AsyncMock()
        return session
    
    def test_client_initialization(self, client):
        """Test MCPClient initialization."""
        assert client._command == "python"
        assert client._args == ["./test_server.py"]
        assert client._env == {"TEST_VAR": "test_value"}
        assert client._session is None
        assert client._exit_stack is not None
    
    @pytest.mark.asyncio
    async def test_connect_success(self, client, mock_session):
        """Test successful connection to MCP server."""
        with patch('any_mcp.core.client.stdio_client') as mock_stdio_client:
            mock_stdio_client.return_value.__aenter__.return_value = (MagicMock(), MagicMock())
            
            with patch('any_mcp.core.client.ClientSession') as mock_client_session:
                mock_client_session.return_value = mock_session
                
                await client.connect()
                
                assert client._session is not None
                mock_session.initialize.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_connect_failure(self, client):
        """Test connection failure handling."""
        with patch('any_mcp.core.client.stdio_client') as mock_stdio_client:
            mock_stdio_client.return_value.__aenter__.side_effect = Exception("Connection failed")
            
            with pytest.raises(Exception, match="Connection failed"):
                await client.connect()
    
    @pytest.mark.asyncio
    async def test_session_access_before_connect(self, client):
        """Test accessing session before connection raises error."""
        with pytest.raises(ConnectionError, match="Client session not initialized"):
            client.session()
    
    @pytest.mark.asyncio
    async def test_list_tools_success(self, client, mock_session, sample_tools):
        """Test successful tool listing."""
        client._session = mock_session
        mock_session.list_tools.return_value = types.ListToolsResult(tools=sample_tools)
        
        tools = await client.list_tools()
        
        assert len(tools) == 2
        assert tools[0].name == "test_tool_1"
        assert tools[1].name == "test_tool_2"
        mock_session.list_tools.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_list_tools_failure(self, client, mock_session):
        """Test tool listing failure handling."""
        client._session = mock_session
        mock_session.list_tools.side_effect = Exception("Tool listing failed")
        
        tools = await client.list_tools()
        
        assert tools == []
    
    @pytest.mark.asyncio
    async def test_call_tool_success(self, client, mock_session, sample_tool_call, sample_tool_result):
        """Test successful tool execution."""
        client._session = mock_session
        mock_session.call_tool.return_value = sample_tool_result
        
        result = await client.call_tool("test_tool_1", {"input": "test"})
        
        assert result == sample_tool_result
        mock_session.call_tool.assert_called_once_with("test_tool_1", {"input": "test"})
    
    @pytest.mark.asyncio
    async def test_call_tool_failure(self, client, mock_session):
        """Test tool execution failure handling."""
        client._session = mock_session
        mock_session.call_tool.side_effect = Exception("Tool execution failed")
        
        result = await client.call_tool("test_tool_1", {"input": "test"})
        
        assert result is None
    
    @pytest.mark.asyncio
    async def test_list_prompts_success(self, client, mock_session):
        """Test successful prompt listing."""
        client._session = mock_session
        mock_prompts = [types.Prompt(name="test_prompt", description="Test prompt")]
        mock_session.list_prompts.return_value = types.ListPromptsResult(prompts=mock_prompts)
        
        prompts = await client.list_prompts()
        
        assert len(prompts) == 1
        assert prompts[0].name == "test_prompt"
        mock_session.list_prompts.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_prompt_success(self, client, mock_session):
        """Test successful prompt retrieval."""
        client._session = mock_session
        mock_messages = [types.PromptMessage(role="user", content="Test message")]
        mock_session.get_prompt.return_value = types.GetPromptResult(messages=mock_messages)
        
        messages = await client.get_prompt("test_prompt", {"arg": "value"})
        
        assert len(messages) == 1
        assert messages[0].role == "user"
        mock_session.get_prompt.assert_called_once_with("test_prompt", {"arg": "value"})
    
    @pytest.mark.asyncio
    async def test_read_resource_success(self, client, mock_session):
        """Test successful resource reading."""
        client._session = mock_session
        mock_content = "Test resource content"
        mock_session.read_resource.return_value = mock_content
        
        content = await client.read_resource("test://resource")
        
        assert content == mock_content
        mock_session.read_resource.assert_called_once_with("test://resource")
    
    @pytest.mark.asyncio
    async def test_cleanup(self, client, mock_session):
        """Test client cleanup."""
        client._session = mock_session
        
        await client.cleanup()
        
        mock_session.aclose.assert_called_once()
        assert client._session is None
    
    @pytest.mark.asyncio
    async def test_context_manager(self, client, mock_session):
        """Test client as async context manager."""
        with patch('any_mcp.core.client.stdio_client') as mock_stdio_client:
            mock_stdio_client.return_value.__aenter__.return_value = (MagicMock(), MagicMock())
            
            with patch('any_mcp.core.client.ClientSession') as mock_client_session:
                mock_client_session.return_value = mock_session
                
                async with client:
                    assert client._session is not None
                
                mock_session.aclose.assert_called_once()


class TestMCPClientIntegration:
    """Integration tests for MCPClient."""
    
    @pytest.mark.asyncio
    async def test_full_connection_lifecycle(self):
        """Test complete connection lifecycle."""
        client = MCPClient("echo", ["hello"], {"TEST": "value"})
        
        # Test that client can be created
        assert client._command == "echo"
        assert client._args == ["hello"]
        assert client._env == {"TEST": "value"}
        
        # Test cleanup without connection
        await client.cleanup()
        assert client._session is None
    
    @pytest.mark.asyncio
    async def test_error_handling_robustness(self):
        """Test error handling robustness."""
        client = MCPClient("nonexistent", ["command"], {})
        
        # Should handle errors gracefully
        tools = await client.list_tools()
        assert tools == []
        
        result = await client.call_tool("test", {})
        assert result is None
