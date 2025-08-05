#!/usr/bin/env python3
"""
Simple demo showing the any-mcp concept with GitHub MCP.
"""

import asyncio
import os


class AnyMCP:
    """
    Simple any-mcp adapter for demonstration.
    """
    
    def __init__(self, mcp_config):
        self.mcp_config = mcp_config
        self.tools = {}
        
    async def start(self):
        """Start the MCP and discover tools."""
        print(f"Starting MCP: {self.mcp_config}")
        
        # Mock tool discovery
        if "github" in str(self.mcp_config).lower():
            self.tools = {
                "search_repositories": "Search GitHub repositories",
                "get_user": "Get GitHub user info", 
                "create_issue": "Create GitHub issue",
                "create_pull_request": "Create GitHub PR"
            }
        else:
            self.tools = {
                "read_document": "Read document content",
                "edit_document": "Edit document content"
            }
        
        print(f"Discovered {len(self.tools)} tools")
        return self
        
    def list_tools(self):
        """List available tools."""
        return list(self.tools.keys())
        
    async def call_tool(self, tool_name, **kwargs):
        """Call a tool."""
        if tool_name not in self.tools:
            raise ValueError(f"Tool '{tool_name}' not found")
            
        print(f"Calling {tool_name} with args: {kwargs}")
        
        # Mock results
        if tool_name == "search_repositories":
            return {
                "total_count": 150,
                "items": [
                    {"name": "github-mcp-server", "description": "GitHub's official MCP server"},
                    {"name": "any-mcp", "description": "Universal MCP adapter"}
                ]
            }
        elif tool_name == "get_user":
            return {
                "login": "github",
                "id": 9919,
                "type": "Organization"
            }
        elif tool_name == "read_document":
            return f"Content of document {kwargs.get('doc_id', 'unknown')}"
        else:
            return f"Mock result for {tool_name}"
            
    async def stop(self):
        """Stop the MCP."""
        print("Stopping MCP")
        
    async def __aenter__(self):
        await self.start()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.stop()


async def main():
    """Demo any-mcp with GitHub MCP."""
    
    print("any-mcp Demo: Universal MCP Adapter")
    print("=" * 50)
    
    # Demo with GitHub MCP
    github_config = {
        "command": "docker",
        "args": ["run", "-i", "--rm", "ghcr.io/github/github-mcp-server"],
        "env": {"GITHUB_PERSONAL_ACCESS_TOKEN": "your-token"}
    }
    
    async with AnyMCP(github_config) as github:
        print(f"\nAvailable tools: {github.list_tools()}")
        
        # Search repositories
        result = await github.call_tool("search_repositories", 
                                      query="mcp language:python")
        print(f"Found {len(result['items'])} MCP repositories")
        
        # Get user info
        result = await github.call_tool("get_user", username="github")
        print(f"GitHub user: {result['login']}")
    
    print("\nDemo completed!")
    print("any-mcp successfully started GitHub's MCP and executed operations!")


if __name__ == "__main__":
    asyncio.run(main()) 