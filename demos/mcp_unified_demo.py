#!/usr/bin/env python3
"""
MCP Unified ToolManager Demo

This demo shows how to use the new MCP-powered ToolManager that replaces
LLMgine's original ToolManager. It demonstrates:

1. Backward compatibility with existing code
2. Local tools via MCP server
3. Third-party MCP server integration
4. Unified tool discovery and execution
"""

import asyncio
import logging
import os
from llmgine.llm.tools import ToolManager, create_mcp_tool_manager
from llmgine.llm.tools.toolCall import ToolCall

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def demo_backward_compatibility():
    """Demonstrate backward compatibility with existing ToolManager interface."""
    print("\n=== Backward Compatibility Demo ===")
    
    # Create ToolManager using the same interface as before
    manager = ToolManager()
    
    # Initialize MCP system (new requirement)
    await manager.initialize()
    
    # Get available tools (same interface as before)
    tools = manager.parse_tools_to_list()
    print(f"Available tools: {len(tools)}")
    
    for tool in tools:
        print(f"  - {tool['function']['name']}: {tool['function']['description']}")
    
    # Execute a tool call (same interface as before)
    if tools:
        tool_name = tools[0]['function']['name']
        print(f"\nTesting tool: {tool_name}")
        
        # Create a test tool call
        if tool_name == "get_weather":
            tool_call = ToolCall(
                name=tool_name,
                arguments={"city": "melbourne"},
                id="test-1"
            )
        elif tool_name == "simple_get_weather":
            tool_call = ToolCall(
                name=tool_name,
                arguments={"city": "Sydney"},
                id="test-2"
            )
        else:
            tool_call = ToolCall(
                name=tool_name,
                arguments={},
                id="test-3"
            )
        
        result = await manager.execute_tool_call(tool_call)
        print(f"Result: {result}")
    
    # Cleanup
    await manager.cleanup()


async def demo_mcp_server_integration():
    """Demonstrate adding third-party MCP servers."""
    print("\n=== MCP Server Integration Demo ===")
    
    # Create manager using factory function
    manager = create_mcp_tool_manager()
    await manager.initialize()
    
    # Add calculator MCP server
    calculator_server = os.path.join(os.path.dirname(__file__), "..", "mcps", "demo_calculator.py")
    if os.path.exists(calculator_server):
        success = await manager.add_mcp_server(
            name="demo-calculator",
            command="python",
            args=[calculator_server],
            env={}
        )
        print(f"Added calculator server: {success}")
        
        # List available tools after adding server
        tools = await manager.list_available_tools()
        print(f"Available tools after adding calculator: {len(tools)}")
        
        # Test calculator tool
        calc_call = ToolCall(
            name="calculate",
            arguments={"expression": "2 + 2 * 3"},
            id="calc-test"
        )
        
        result = await manager.execute_tool_call(calc_call)
        print(f"Calculator result: {result}")
    
    # List all MCP servers
    servers = await manager.list_mcp_servers()
    print(f"\nActive MCP servers:")
    for name, status in servers.items():
        print(f"  - {name}: {'Connected' if status else 'Disconnected'}")
    
    await manager.cleanup()


async def demo_notion_integration():
    """Demonstrate Notion MCP server integration (if available)."""
    print("\n=== Notion Integration Demo ===")
    
    # Check if Notion token is available
    notion_token = os.getenv("NOTION_API_TOKEN")
    if not notion_token:
        print("NOTION_API_TOKEN not set, skipping Notion demo")
        return
    
    manager = create_mcp_tool_manager()
    await manager.initialize()
    
    # Add Notion MCP server
    try:
        success = await manager.add_mcp_server(
            name="notion-official",
            command="npx",
            args=["@notionhq/notion-mcp-server"],
            env={"NOTION_TOKEN": notion_token}
        )
        
        if success:
            print("Added Notion MCP server successfully")
            
            # List available Notion tools
            tools = await manager.list_available_tools()
            notion_tools = [t for t in tools if t.get("mcp_name") == "notion-official"]
            print(f"Notion tools available: {len(notion_tools)}")
            
            for tool in notion_tools[:5]:  # Show first 5 tools
                print(f"  - {tool['tool_name']}: {tool.get('description', 'No description')}")
            
        else:
            print("Failed to add Notion MCP server - check if @notionhq/notion-mcp-server is installed")
    
    except Exception as e:
        print(f"Error with Notion integration: {e}")
    
    await manager.cleanup()


async def demo_tool_discovery():
    """Demonstrate comprehensive tool discovery across all MCP servers."""
    print("\n=== Tool Discovery Demo ===")
    
    manager = create_mcp_tool_manager()
    await manager.initialize()
    
    # Get comprehensive tool information
    tools = await manager.list_available_tools()
    schemas = manager.parse_tools_to_list()
    
    print(f"Total tools available: {len(tools)}")
    print(f"OpenAI schemas generated: {len(schemas)}")
    
    # Group tools by MCP server
    server_tools = {}
    for tool in tools:
        server = tool.get("mcp_name", "unknown")
        if server not in server_tools:
            server_tools[server] = []
        server_tools[server].append(tool["tool_name"])
    
    print("\nTools by MCP server:")
    for server, tool_names in server_tools.items():
        print(f"  {server}: {', '.join(tool_names)}")
    
    await manager.cleanup()


async def main():
    """Run all demos."""
    print("MCP Unified ToolManager Demo")
    print("=" * 50)
    
    try:
        await demo_backward_compatibility()
        await demo_mcp_server_integration() 
        await demo_tool_discovery()
        await demo_notion_integration()
        
    except Exception as e:
        logger.error(f"Demo failed: {e}", exc_info=True)
    
    print("\n" + "=" * 50)
    print("Demo completed!")


if __name__ == "__main__":
    asyncio.run(main())