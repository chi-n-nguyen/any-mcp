"""
MCP-powered tools for litellm.

This module provides a unified MCP-powered ToolManager that replaces
the original implementation while maintaining 100% backward compatibility.
"""

from llmgine.llm.tools.mcp_unified_tool_manager import MCPUnifiedToolManager as ToolManager
from llmgine.llm.tools.mcp_unified_tool_manager import create_mcp_tool_manager
from llmgine.llm.tools.toolCall import ToolCall

# Legacy imports for backward compatibility
from llmgine.llm.tools.tool_manager import ToolManager as LegacyToolManager
from llmgine.llm.tools.enhanced_tool_manager import EnhancedToolManager

__all__ = [
    "ToolCall",
    "ToolManager",  # Now points to MCPUnifiedToolManager
    "create_mcp_tool_manager",
    "LegacyToolManager",  # For migration period
    "EnhancedToolManager",  # For migration period
]