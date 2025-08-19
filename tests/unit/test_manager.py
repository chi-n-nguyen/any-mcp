"""
Unit tests for MCP manager functionality
"""
import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from pathlib import Path

from any_mcp.managers.manager import MCPManager
from any_mcp.managers.installer import MCPInstaller, MCPConfig, MCPType
from any_mcp.core.client import MCPClient


class TestMCPManager:
    """Test cases for MCPManager class."""
    
    @pytest.fixture
    def manager(self, sample_mcp_config):
        """Create a fresh MCPManager instance for each test."""
        return MCPManager(sample_mcp_config)
    
    @pytest.fixture
    def mock_installer(self):
        """Create a mock MCPInstaller."""
        installer = AsyncMock(spec=MCPInstaller)
        installer.get_enabled_mcps.return_value = []
        installer.get_mcp_config.return_value = None
        return installer
    
    @pytest.fixture
    def enabled_mcp_config(self):
        """Create an enabled MCP configuration."""
        return MCPConfig(
            name="test-mcp",
            type=MCPType.LOCAL,
            source="./test_server.py",
            description="Test MCP server",
            env_vars={"TEST_VAR": "test_value"},
            enabled=True
        )
    
    def test_manager_initialization(self, manager):
        """Test MCPManager initialization."""
        assert manager.installer is not None
        assert manager.active_clients == {}
        assert manager._initialized is False
        assert manager.exit_stack is not None
    
    @pytest.mark.asyncio
    async def test_initialize_success(self, manager, mock_installer, enabled_mcp_config):
        """Test successful manager initialization."""
        manager.installer = mock_installer
        mock_installer.get_enabled_mcps.return_value = [enabled_mcp_config]
        
        with patch.object(manager, 'setup_mcp', return_value=True) as mock_setup:
            await manager.initialize()
            
            assert manager._initialized is True
            mock_setup.assert_called_once_with("test-mcp")
    
    @pytest.mark.asyncio
    async def test_initialize_already_initialized(self, manager):
        """Test initialization when already initialized."""
        manager._initialized = True
        
        await manager.initialize()
        
        # Should return early without re-initializing
        assert manager._initialized is True
    
    @pytest.mark.asyncio
    async def test_initialize_failure(self, manager, mock_installer):
        """Test initialization failure handling."""
        manager.installer = mock_installer
        mock_installer.get_enabled_mcps.side_effect = Exception("Initialization failed")
        
        with pytest.raises(Exception, match="Initialization failed"):
            await manager.initialize()
        
        assert manager._initialized is False
    
    @pytest.mark.asyncio
    async def test_setup_mcp_already_active(self, manager):
        """Test setting up an already active MCP."""
        manager.active_clients["test-mcp"] = MagicMock()
        
        result = await manager.setup_mcp("test-mcp")
        
        assert result is True
    
    @pytest.mark.asyncio
    async def test_setup_mcp_not_found(self, manager, mock_installer):
        """Test setting up a non-existent MCP."""
        manager.installer = mock_installer
        mock_installer.get_mcp_config.return_value = None
        
        result = await manager.setup_mcp("nonexistent")
        
        assert result is False
    
    @pytest.mark.asyncio
    async def test_setup_mcp_disabled(self, manager, mock_installer):
        """Test setting up a disabled MCP."""
        disabled_config = MCPConfig(
            name="disabled-mcp",
            type=MCPType.LOCAL,
            source="./test_server.py",
            description="Disabled MCP server",
            env_vars={},
            enabled=False
        )
        
        manager.installer = mock_installer
        mock_installer.get_mcp_config.return_value = disabled_config
        
        result = await manager.setup_mcp("disabled-mcp")
        
        assert result is False
    
    @pytest.mark.asyncio
    async def test_setup_local_mcp_success(self, manager, enabled_mcp_config):
        """Test successful local MCP setup."""
        with patch.object(manager, '_setup_local_mcp', return_value=MagicMock()) as mock_setup:
            result = await manager.setup_mcp("test-mcp")
            
            assert result is True
            mock_setup.assert_called_once_with(enabled_mcp_config)
    
    @pytest.mark.asyncio
    async def test_setup_docker_mcp_success(self, manager):
        """Test successful Docker MCP setup."""
        docker_config = MCPConfig(
            name="docker-mcp",
            type=MCPType.DOCKER,
            source="test:latest",
            description="Docker MCP server",
            env_vars={},
            enabled=True
        )
        
        with patch.object(manager, '_setup_docker_mcp', return_value=MagicMock()) as mock_setup:
            result = await manager.setup_mcp("docker-mcp")
            
            assert result is True
            mock_setup.assert_called_once_with(docker_config)
    
    @pytest.mark.asyncio
    async def test_setup_unsupported_type(self, manager, mock_installer):
        """Test setting up an unsupported MCP type."""
        unsupported_config = MCPConfig(
            name="unsupported-mcp",
            type="unsupported",
            source="./test_server.py",
            description="Unsupported MCP server",
            env_vars={},
            enabled=True
        )
        
        manager.installer = mock_installer
        mock_installer.get_mcp_config.return_value = unsupported_config
        
        result = await manager.setup_mcp("unsupported-mcp")
        
        assert result is False
    
    @pytest.mark.asyncio
    async def test_setup_mcp_failure(self, manager, enabled_mcp_config):
        """Test MCP setup failure handling."""
        with patch.object(manager, '_setup_local_mcp', return_value=None) as mock_setup:
            result = await manager.setup_mcp("test-mcp")
            
            assert result is False
            mock_setup.assert_called_once_with(enabled_mcp_config)
    
    @pytest.mark.asyncio
    async def test_setup_local_mcp_success(self, manager, enabled_mcp_config):
        """Test successful local MCP setup."""
        mock_client = AsyncMock(spec=MCPClient)
        
        with patch('any_mcp.managers.manager.MCPClient', return_value=mock_client):
            with patch.object(mock_client, 'connect'):
                result = await manager._setup_local_mcp(enabled_mcp_config)
                
                assert result == mock_client
                mock_client.connect.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_setup_local_mcp_failure(self, manager, enabled_mcp_config):
        """Test local MCP setup failure handling."""
        with patch('any_mcp.managers.manager.MCPClient') as mock_client_class:
            mock_client_class.side_effect = Exception("Client creation failed")
            
            result = await manager._setup_local_mcp(enabled_mcp_config)
            
            assert result is None
    
    @pytest.mark.asyncio
    async def test_setup_docker_mcp_success(self, manager):
        """Test successful Docker MCP setup."""
        docker_config = MCPConfig(
            name="docker-mcp",
            type=MCPType.DOCKER,
            source="test:latest",
            description="Docker MCP server",
            env_vars={"DOCKER_VAR": "docker_value"},
            enabled=True
        )
        
        mock_client = AsyncMock(spec=MCPClient)
        
        with patch('any_mcp.managers.manager.MCPClient', return_value=mock_client):
            with patch.object(mock_client, 'connect'):
                result = await manager._setup_docker_mcp(docker_config)
                
                assert result == mock_client
                mock_client.connect.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_call_mcp_success(self, manager, mock_mcp_client, sample_tool_call, sample_tool_result):
        """Test successful MCP tool call."""
        manager.active_clients["test-mcp"] = mock_mcp_client
        mock_mcp_client.call_tool.return_value = sample_tool_result
        
        result = await manager.call_mcp("test-mcp", "test_tool", {"input": "test"})
        
        assert result == sample_tool_result
        mock_mcp_client.call_tool.assert_called_once_with("test_tool", {"input": "test"})
    
    @pytest.mark.asyncio
    async def test_call_mcp_not_found(self, manager):
        """Test MCP tool call when MCP not found."""
        result = await manager.call_mcp("nonexistent", "test_tool", {})
        
        assert result is None
    
    @pytest.mark.asyncio
    async def test_get_active_mcps(self, manager):
        """Test getting active MCPs."""
        manager.active_clients = {"mcp1": MagicMock(), "mcp2": MagicMock()}
        
        active_mcps = manager.get_active_mcps()
        
        assert active_mcps == ["mcp1", "mcp2"]
    
    @pytest.mark.asyncio
    async def test_cleanup(self, manager):
        """Test manager cleanup."""
        mock_client = AsyncMock(spec=MCPClient)
        manager.active_clients["test-mcp"] = mock_client
        
        await manager.cleanup()
        
        mock_client.aclose.assert_called_once()
        assert manager.active_clients == {}
        assert manager._initialized is False
    
    @pytest.mark.asyncio
    async def test_context_manager(self, manager):
        """Test manager as async context manager."""
        async with manager:
            assert manager._initialized is True
        
        assert manager._initialized is False


class TestMCPManagerIntegration:
    """Integration tests for MCPManager."""
    
    @pytest.mark.asyncio
    async def test_full_lifecycle(self, sample_mcp_config):
        """Test complete manager lifecycle."""
        manager = MCPManager(sample_mcp_config)
        
        # Test initialization
        assert manager._initialized is False
        
        # Test cleanup without initialization
        await manager.cleanup()
        assert manager._initialized is False
    
    @pytest.mark.asyncio
    async def test_error_handling_robustness(self, sample_mcp_config):
        """Test error handling robustness."""
        manager = MCPManager(sample_mcp_config)
        
        # Should handle errors gracefully
        result = await manager.call_mcp("nonexistent", "tool", {})
        assert result is None
        
        # Should not crash on invalid operations
        active_mcps = manager.get_active_mcps()
        assert active_mcps == []
