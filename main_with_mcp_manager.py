#!/usr/bin/env python3
"""
Enhanced main.py that uses MCPManager for Nathan's final destination workflow.
This integrates MCP discovery, installation, and LLM tool registration.
"""

import asyncio
import sys
import os
from dotenv import load_dotenv
from contextlib import AsyncExitStack

# MCP Infrastructure
from mcp_manager import MCPManager
from mcp_installer import MCPInstaller
from core.claude import Claude
from core.cli_chat import CliChat
from core.cli import CliApp

load_dotenv()

# Anthropic Config
claude_model = os.getenv("CLAUDE_MODEL", "claude-3-5-sonnet-20241022")
anthropic_api_key = os.getenv("ANTHROPIC_API_KEY", "")

assert claude_model, "Error: CLAUDE_MODEL cannot be empty. Update .env"
assert anthropic_api_key, (
    "Error: ANTHROPIC_API_KEY cannot be empty. Update .env"
)


async def call_mcp(args):
    """
    Nathan's call_mcp function - demonstrates direct MCP calling.
    This is equivalent to: call_mcp(args)
    """
    manager = MCPManager()
    async with manager:
        # Get available tools from all MCPs
        all_tools = await manager.list_all_tools()
        
        print(f"Available MCPs: {list(all_tools.keys())}")
        for mcp_name, tools in all_tools.items():
            print(f"  {mcp_name}: {len(tools)} tools")
            
        # Example: call a GitHub tool if available
        if "github" in manager.get_active_mcps():
            try:
                result = await manager.call_mcp("github", "search_repositories", args)
                print(f"MCP call result: {result}")
                return result
            except Exception as e:
                print(f"MCP call failed: {e}")
        
        return None


def push_tool(args):
    """
    Nathan's push_tool function - represents getting tools from MCP.
    This is equivalent to: from mcp.github import push_tool; push_tool(args)
    """
    print(f"push_tool called with args: {args}")
    # In Nathan's vision, this would return the actual tool function
    # that can be registered with the LLM
    return "github_tool_function"


class LLMRegistry:
    """Represents Nathan's llm.register interface."""
    
    def __init__(self, claude_service):
        self.claude_service = claude_service
        self.registered_tools = []
    
    def tool(self, tool_func):
        """Register a tool with the LLM - llm.register.tool(push_tool)"""
        print(f"Registering tool with LLM: {tool_func}")
        self.registered_tools.append(tool_func)
        return tool_func


async def nathan_main_workflow():
    """
    Nathan's exact workflow:
    def main():
        call_mcp(args)
        from mcp.github import push_tool
        push_tool(args)  
        llm.register.tool(push_tool)
    """
    print("🎯 Executing Nathan's Main Workflow")
    print("=" * 40)
    
    # Nathan's args
    args = {"query": "mcp language:python", "sort": "stars"}
    
    # Step 1: call_mcp(args)
    print("📞 Step 1: call_mcp(args)")
    result = await call_mcp(args)
    print(f"   Result: {result}\n")
    
    # Step 2: from mcp.github import push_tool
    print("📦 Step 2: from mcp.github import push_tool")
    # In our architecture, this is getting the tool from the MCP
    github_tool = push_tool(args)
    print(f"   Imported tool: {github_tool}\n")
    
    # Step 3: llm.register.tool(push_tool)
    print("🤖 Step 3: llm.register.tool(push_tool)")
    claude_service = Claude(model=claude_model)
    llm_registry = LLMRegistry(claude_service)
    llm_registry.tool(github_tool)
    print(f"   Registered {len(llm_registry.registered_tools)} tools with LLM\n")
    
    print("✅ Nathan's workflow completed successfully!")


async def main():
    """Enhanced main that supports both old CLI mode and Nathan's workflow."""
    
    # Check if we should run Nathan's workflow demo
    if "--nathan-demo" in sys.argv:
        await nathan_main_workflow()
        return
    
    # Otherwise, run the enhanced CLI with MCP Manager
    claude_service = Claude(model=claude_model)
    
    # Initialize MCP Manager with configuration
    mcp_manager = MCPManager()
    
    async with AsyncExitStack() as stack:
        # Setup MCP Manager
        await stack.enter_async_context(mcp_manager)
        
        # Convert MCP clients to the format expected by CliChat
        clients = {
            f"mcp_{name}": client 
            for name, client in mcp_manager.active_clients.items()
        }
        
        # Add the default document client if no MCPs are active
        if not clients:
            from mcp_client import MCPClient
            command, args = (
                ("uv", ["run", "mcp_server.py"])
                if os.getenv("USE_UV", "0") == "1"
                else ("python", ["mcp_server.py"])
            )
            doc_client = await stack.enter_async_context(
                MCPClient(command=command, args=args)
            )
            clients["doc_client"] = doc_client
        
        # Create chat interface
        chat = CliChat(
            doc_client=list(clients.values())[0],  # Use first client as doc_client
            clients=clients,
            claude_service=claude_service,
        )

        # Create and run CLI
        cli = CliApp(chat)
        await cli.initialize()
        
        print("\n🚀 any-mcp Enhanced CLI Ready!")
        print("📋 Available MCPs:")
        
        status = await mcp_manager.get_mcp_status()
        for name, info in status.items():
            emoji = "✅" if info["active"] and info["healthy"] else "❌"
            print(f"   {emoji} {name}: {info['description']}")
        
        if "--nathan-demo" not in sys.argv:
            print("\n💡 Tips:")
            print("   • All MCP tools are automatically available to Claude")
            print("   • Type your queries naturally - Claude will use appropriate tools")
            print("   • Use --nathan-demo flag to see Nathan's workflow demo")
            print("   • MCPs are configured in mcp_config.yaml")
        
        await cli.run()


if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()