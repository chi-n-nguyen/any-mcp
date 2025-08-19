#!/usr/bin/env python3
"""
Simple Interactive Demo - See Local vs MCP Tools in Action

This demo shows how the hybrid system works with both local Python functions
and MCP tools from external servers.
"""

import asyncio
import os
import sys

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from llmgine.llm.tools.tool_manager import ToolManager
from llmgine.llm.tools.toolCall import ToolCall


# Simple local tools
def local_add(x: int, y: int) -> int:
    """Add two numbers locally (Python function)."""
    return x + y


def local_greet(name: str) -> str:
    """Greet someone locally (Python function)."""
    return f"👋 Hello {name}! (from local Python function)"


async def main():
    print("🚀 HYBRID TOOL SYSTEM DEMO")
    print("=" * 50)
    print("This shows local Python functions + MCP tools working together!")
    print()
    
    # Create tool manager
    tool_manager = ToolManager()
    
    # Register local tools
    print("📝 REGISTERING LOCAL TOOLS...")
    tool_manager.register_tool(local_add)
    tool_manager.register_tool(local_greet)
    print(f"✅ Registered {len(tool_manager.tools)} local tools")
    print()
    
    # Register MCP calculator server
    print("🚀 STARTING MCP CALCULATOR SERVER...")
    mcp_success = await tool_manager.register_mcp_server(
        server_name="calculator",
        command=sys.executable,
        args=[os.path.join(os.path.dirname(__file__), "mcps", "demo_calculator.py")]
    )
    
    if mcp_success:
        print(f"✅ MCP server started with {len(tool_manager.tools) - 2} MCP tools")
    else:
        print("❌ Failed to start MCP server")
        return
    
    print()
    
    # Show what we have
    print("🛠️  ALL AVAILABLE TOOLS:")
    for i, tool_name in enumerate(tool_manager.tools.keys(), 1):
        if tool_name in ['local_add', 'local_greet']:
            print(f"  {i}. {tool_name} (LOCAL Python function)")
        else:
            print(f"  {i}. {tool_name} (MCP external server)")
    
    print()
    print("🧪 LET'S TEST THEM!")
    print()
    
    # Test local tools
    print("🔵 TESTING LOCAL TOOLS:")
    print("  local_add(5, 3) =", await tool_manager.execute_tool_call(
        ToolCall(id="1", name="local_add", arguments={"x": 5, "y": 3})
    ))
    print("  local_greet('World') =", await tool_manager.execute_tool_call(
        ToolCall(id="2", name="local_greet", arguments={"name": "World"})
    ))
    print()
    
    # Test MCP tools
    print("🟡 TESTING MCP TOOLS:")
    print("  add(10, 20) =", await tool_manager.execute_tool_call(
        ToolCall(id="3", name="add", arguments={"a": 10, "b": 20})
    ))
    print("  multiply(6, 7) =", await tool_manager.execute_tool_call(
        ToolCall(id="4", name="multiply", arguments={"a": 6, "b": 7})
    ))
    print("  power(2, 8) =", await tool_manager.execute_tool_call(
        ToolCall(id="5", name="power", arguments={"base": 2, "exponent": 8})
    ))
    print()
    
    # Test mixed tool calls
    print("🔄 TESTING MIXED TOOL CALLS (local + MCP together):")
    mixed_calls = [
        ToolCall(id="6", name="local_add", arguments={"x": 100, "y": 200}),
        ToolCall(id="7", name="add", arguments={"a": 50, "b": 50}),
        ToolCall(id="8", name="local_greet", arguments={"name": "Hybrid System"}),
    ]
    
    results = await tool_manager.execute_tool_calls(mixed_calls)
    for i, (call, result) in enumerate(zip(mixed_calls, results)):
        print(f"  {call.name}: {result}")
    
    print()
    print("🎉 WHAT JUST HAPPENED?")
    print("=" * 50)
    print("1. Local tools run as regular Python functions (fast, reliable)")
    print("2. MCP tools run in external subprocess servers (isolated, extensible)")
    print("3. Both look the same to LLMs - they just call tools!")
    print("4. ToolManager handles both types seamlessly")
    print()
    print("💡 BENEFITS:")
    print("  ✅ Keep existing local tools (no breaking changes)")
    print("  ✅ Add external MCP tools when needed")
    print("  ✅ Process isolation for MCP tools")
    print("  ✅ Unified interface for all tools")
    print()
    
    # Cleanup
    print("🧹 Cleaning up MCP servers...")
    await tool_manager.cleanup_mcp_servers()
    print("Done! 🎯")


if __name__ == "__main__":
    asyncio.run(main())
