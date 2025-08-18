"""
Pytest configuration and fixtures for any-mcp testing
"""
import pytest
import asyncio
import tempfile
import os
from pathlib import Path
from typing import Dict, Any, AsyncGenerator
from unittest.mock import AsyncMock, MagicMock

from any_mcp.core.client import MCPClient
from any_mcp.managers.manager import MCPManager
from any_mcp.managers.installer import MCPInstaller, MCPConfig, MCPType


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def temp_config_dir():
    """Create a temporary directory for test configuration files."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield temp_dir


@pytest.fixture
def sample_mcp_config(temp_config_dir):
    """Create a sample MCP configuration for testing."""
    config_path = Path(temp_config_dir) / "test_mcp_config.yaml"
    
    config_content = """
installed_mcps:
  test-calculator:
    type: "local"
    source: "./mcps/demo_calculator.py"
    description: "Test calculator MCP server"
    env_vars: {}
    enabled: true
    
  test-notion:
    type: "local"
    source: "./mcps/notion_mcp_server.py"
    description: "Test Notion MCP server"
    env_vars:
      NOTION_TOKEN: "test_token"
    enabled: false
"""
    
    config_path.write_text(config_content)
    return str(config_path)


@pytest.fixture
def mock_mcp_config():
    """Create a mock MCP configuration object."""
    return MCPConfig(
        name="test-mcp",
        type=MCPType.LOCAL,
        source="./test_server.py",
        description="Test MCP server",
        env_vars={"TEST_VAR": "test_value"},
        enabled=True
    )


@pytest.fixture
def mock_mcp_client():
    """Create a mock MCP client for testing."""
    client = AsyncMock(spec=MCPClient)
    client._command = "python"
    client._args = ["./test_server.py"]
    client._env = {"TEST_VAR": "test_value"}
    return client


@pytest.fixture
def mock_mcp_manager(sample_mcp_config):
    """Create a mock MCP manager for testing."""
    manager = MCPManager(sample_mcp_config)
    manager.installer = AsyncMock(spec=MCPInstaller)
    return manager


@pytest.fixture
def mock_installer():
    """Create a mock MCP installer for testing."""
    installer = AsyncMock(spec=MCPInstaller)
    installer.get_enabled_mcps.return_value = []
    installer.get_mcp_config.return_value = None
    return installer


@pytest.fixture
def test_env_vars():
    """Set up test environment variables."""
    original_env = os.environ.copy()
    
    # Set test environment variables
    test_vars = {
        "TEST_VAR": "test_value",
        "ANTHROPIC_API_KEY": "test_claude_key",
        "GOOGLE_API_KEY": "test_gemini_key",
        "NOTION_API_TOKEN": "test_notion_token"
    }
    
    os.environ.update(test_vars)
    
    yield test_vars
    
    # Restore original environment
    os.environ.clear()
    os.environ.update(original_env)


@pytest.fixture
def async_context():
    """Provide async context for testing."""
    async def _async_context():
        return True
    
    return _async_context


# Test data fixtures
@pytest.fixture
def sample_tools():
    """Sample MCP tools for testing."""
    from mcp.types import Tool
    
    return [
        Tool(
            name="test_tool_1",
            description="First test tool",
            inputSchema={
                "type": "object",
                "properties": {
                    "input": {"type": "string"}
                },
                "required": ["input"]
            }
        ),
        Tool(
            name="test_tool_2", 
            description="Second test tool",
            inputSchema={
                "type": "object",
                "properties": {
                    "number": {"type": "number"}
                },
                "required": ["number"]
            }
        )
    ]


@pytest.fixture
def sample_tool_call():
    """Sample tool call data for testing."""
    return {
        "name": "test_tool_1",
        "arguments": {"input": "test_input"}
    }


@pytest.fixture
def sample_tool_result():
    """Sample tool result data for testing."""
    from mcp.types import CallToolResult, TextContent
    
    return CallToolResult(
        content=[TextContent(type="text", text="test_result")]
    )
