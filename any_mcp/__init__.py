"""
any-mcp: Universal adapter for MCP (Model Context Protocol) packages.

This package provides a unified interface for managing and interacting with
various MCP servers and tools.
"""

__version__ = "1.0.0"
__author__ = "AI @ dscubed"
__email__ = "contact@dscubed.ai"

from any_mcp.core.client import MCPClient
from any_mcp.managers.manager import MCPManager

__all__ = ["MCPClient", "MCPManager"]
