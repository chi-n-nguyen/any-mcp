"""
Unified MCP-powered tools for LLMgine.

This module provides a unified MCP-powered ToolManager that provides access
to both local tools and third-party MCP servers through a single interface.
"""

from llmgine.llm.tools.mcp_unified_tool_manager import MCPUnifiedToolManager as ToolManager
from llmgine.llm.tools.mcp_unified_tool_manager import create_mcp_tool_manager
from llmgine.llm.tools.toolCall import ToolCall

__all__ = [
    "ToolCall",
    "ToolManager",
    "create_mcp_tool_manager",
]