"""
Universal MCP Adapter

A universal adapter layer that enables LLMs to plug-and-play with any third-party MCP
(Model Context Protocol) without bespoke coding.
"""

__version__ = "0.1.0"
__author__ = "chi-n-nguyen"

from .core.adapter import UniversalMCPAdapter
from .core.types import MCPToolSpec, MCPResponse, MCPError

__all__ = [
    "UniversalMCPAdapter",
    "MCPToolSpec", 
    "MCPResponse",
    "MCPError",
] 