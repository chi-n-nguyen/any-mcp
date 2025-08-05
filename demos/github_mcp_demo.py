#!/usr/bin/env python3
"""
Demo script showing any-mcp working with GitHub's official MCP server.
"""

import asyncio
import sys
import os
from pathlib import Path

# Add the src directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from any_mcp import AnyMCP


async def main():
    """Demo the any-mcp adapter with GitHub's MCP server."""
    
    print("Starting any-mcp demo with GitHub MCP server...")
    print("Using GitHub's official MCP server")
    print()
    
    # GitHub MCP server configuration
    # You can run it via Docker or download the binary
    github_mcp_config = {
        "command": "docker",
        "args": [
            "run", "-i", "--rm",
            "-e", "GITHUB_PERSONAL_ACCESS_TOKEN",
            "ghcr.io/github/github-mcp-server"
        ],
        "env": {
            "GITHUB_PERSONAL_ACCESS_TOKEN": os.getenv("GITHUB_TOKEN", "your-token-here")
        }
    }
    
    async with AnyMCP(github_mcp_config) as github:
        # Discover available tools
        tools = github.list_tools()
        print(f"Discovered GitHub tools: {len(tools)} tools available")
        print(f"Sample tools: {tools[:5]}...")  # Show first 5 tools
        print()
        
        # Demo some GitHub operations
        print("Using GitHub tools...")
        
        # Search repositories
        result = await github.call_tool("search_repositories", 
                                      query="mcp language:python stars:>100")
        print(f"Found {len(result.get('items', []))} MCP repositories")
        
        # Get user info
        result = await github.call_tool("get_user", username="github")
        print(f"GitHub user: {result.get('login', 'Unknown')}")
        
        print()
        print("Demo completed successfully!")
        print("any-mcp successfully started GitHub's MCP server and executed operations!")


if __name__ == "__main__":
    asyncio.run(main()) 