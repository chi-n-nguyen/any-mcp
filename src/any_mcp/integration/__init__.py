"""
llmgine Integration Layer for any-mcp

This package provides seamless integration between any-mcp and llmgine,
allowing any-mcp to function as a llmgine engine with full tool support.
"""

__version__ = "1.0.0"

from .engine import AnyMCPEngine
from .tool_adapter import LLMgineToolAdapter
from .message_bridge import MessageBridge

__all__ = [
    "AnyMCPEngine",
    "LLMgineToolAdapter", 
    "MessageBridge"
]
