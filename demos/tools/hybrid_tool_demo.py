#!/usr/bin/env python3
"""
Hybrid Tool Demo - Local + MCP Tools Together

Shows how the extended ToolManager can use both local Python functions
and MCP tools from external servers.
"""

import asyncio
import os
import sys

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from llmgine.llm.tools.tool_manager import ToolManager
from llmgine.llm.tools.toolCall import ToolCall


# Define some local tools (regular Python functions)
def greet(name: str) -> str:
    """Greet someone by name."""
    return f"Hello, {name}!"


def local_multiply(x: int, y: int) -> int:
    """Multiply two numbers locally."""
    return x * y


async def async_weather(city: str) -> str:
    """Get fake weather for a city (async function)."""
    await asyncio.sleep(0.1)  # Simulate async work
    return f"The weather in {city} is sunny and 72°F"


async def main():
    print("🔧 Hybrid Tool Demo - Local + MCP Tools")
    print("=" * 50)
    
    # Create tool manager
    tool_manager = ToolManager()
    
    # Register local tools
    print("📝 Registering local tools...")
    tool_manager.register_tool(greet)
    tool_manager.register_tool(local_multiply)
    tool_manager.register_tool(async_weather)
    print(f"✅ Registered {len(tool_manager.tools)} local tools")
    
    # Register MCP server (calculator)
    print("\n🚀 Starting MCP calculator server...")
    mcp_success = await tool_manager.register_mcp_server(
        server_name="calculator",
        command=sys.executable,
        args=[os.path.join(os.path.dirname(__file__), "mcps", "demo_calculator.py")]
    )
    
    if mcp_success:
        print(f"✅ MCP server registered with {len(tool_manager.tools) - 3} MCP tools")
    else:
        print("❌ Failed to register MCP server")
        return
    
    # Show all available tools
    print(f"\n🛠️  Total tools available: {len(tool_manager.tools)}")
    for tool_name in tool_manager.tools.keys():
        print(f"  - {tool_name}")
    
    print(f"\n📋 Tool schemas for LLM: {len(tool_manager.tool_schemas)} schemas")
    
    # Test local tools
    print("\n🧪 Testing local tools:")
    
    # Test sync local tool
    result = await tool_manager.execute_tool_call(
        ToolCall(id="1", name="greet", arguments={"name": "World"})
    )
    print(f"greet('World') = {result}")
    
    # Test async local tool
    result = await tool_manager.execute_tool_call(
        ToolCall(id="2", name="async_weather", arguments={"city": "San Francisco"})
    )
    print(f"async_weather('San Francisco') = {result}")
    
    # Test local math
    result = await tool_manager.execute_tool_call(
        ToolCall(id="3", name="local_multiply", arguments={"x": 7, "y": 8})
    )
    print(f"local_multiply(7, 8) = {result}")
    
    # Test MCP tools
    print("\n🔌 Testing MCP tools:")
    
    # Test MCP add
    result = await tool_manager.execute_tool_call(
        ToolCall(id="4", name="add", arguments={"a": 15, "b": 27})
    )
    print(f"add(15, 27) = {result}")
    
    # Test MCP sqrt  
    result = await tool_manager.execute_tool_call(
        ToolCall(id="5", name="sqrt", arguments={"number": 64})
    )
    print(f"sqrt(64) = {result}")
    
    # Test multiple tool calls together
    print("\n🔄 Testing multiple tool calls:")
    tool_calls = [
        ToolCall(id="6", name="greet", arguments={"name": "MCP"}),
        ToolCall(id="7", name="multiply", arguments={"a": 6, "b": 7}),
        ToolCall(id="8", name="local_multiply", arguments={"x": 5, "y": 4}),
    ]
    
    results = await tool_manager.execute_tool_calls(tool_calls)
    for i, result in enumerate(results):
        print(f"  {tool_calls[i].name}: {result}")
    
    print("\n✅ Hybrid tool system working! Local and MCP tools coexist perfectly.")
    
    # Cleanup
    print("\n🧹 Cleaning up MCP servers...")
    await tool_manager.cleanup_mcp_servers()
    print("Done!")


if __name__ == "__main__":
    asyncio.run(main())
