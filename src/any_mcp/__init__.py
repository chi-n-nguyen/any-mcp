"""
any-mcp: A small program that safely starts any MCP package, figures out what tools it offers, and lets you use them through one simple interface.
"""

__version__ = "0.1.0"
__author__ = "chi-n-nguyen"

from .adapter import AnyMCP

__all__ = ["AnyMCP"] 