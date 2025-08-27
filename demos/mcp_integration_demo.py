#!/usr/bin/env python3
"""
MCP Integration Demo

This script demonstrates the MCP integration with LLMgine, showing:
1. How to set up the enhanced tool manager
2. How to register local tools
3. How to add MCP servers
4. How to execute tools through the unified interface
5. How to monitor tool execution and server health

Run this script to see the MCP integration in action.
"""

import asyncio
import sys
import os
from typing import List

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from llmgine.llm.context.memory import SimpleChatHistory
from llmgine.llm.tools.enhanced_tool_manager import (
    EnhancedToolManager,
    MCPServerConfig,
    create_enhanced_tool_manager_with_servers
)
from llmgine.llm.tools.toolCall import ToolCall


# Example local tools
def get_current_time() -> str:
    """Get the current time."""
    import datetime
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def reverse_string(text: str) -> str:
    """Reverse a string."""
    return text[::-1]


def count_words(text: str) -> int:
    """Count words in a text."""
    return len(text.split())


async def demo_basic_setup():
    """Demonstrate basic setup of enhanced tool manager."""
    print("🚀 Demo 1: Basic Enhanced Tool Manager Setup")
    print("=" * 50)
    
    # Create chat history
    chat_history = SimpleChatHistory()
    chat_history.set_system_prompt("You are a helpful assistant with access to tools.")
    
    # Create enhanced tool manager
    tool_manager = EnhancedToolManager(chat_history)
    
    # Register local tools
    tool_manager.register_tool(get_current_time)
    tool_manager.register_tool(reverse_string)
    tool_manager.register_tool(count_words)
    
    print(f"✅ Created tool manager with {len(tool_manager.tools)} local tools")
    
    # Test local tool execution
    tool_call = ToolCall(
        id="demo_1",
        name="reverse_string",
        arguments='{"text": "Hello, MCP Integration!"}'
    )
    
    result = await tool_manager.execute_tool_call(tool_call)
    print(f"🔧 Executed local tool 'reverse_string': {result}")
    
    # List all tools
    tools_info = await tool_manager.list_all_tools()
    print(f"📋 Tool summary: {len(tools_info['local_tools'])} local, {len(tools_info['mcp_tools'])} MCP")
    
    print("✅ Demo 1 completed successfully!\n")
    return tool_manager


async def demo_mcp_integration(tool_manager: EnhancedToolManager):
    """Demonstrate MCP server integration."""
    print("🔌 Demo 2: MCP Server Integration")
    print("=" * 50)
    
    # Initialize MCP system
    mcp_success = await tool_manager.initialize_mcp()
    if mcp_success:
        print("✅ MCP system initialized successfully")
    else:
        print("❌ Failed to initialize MCP system")
        return
    
    # Add MCP server (calculator)
    calculator_success = await tool_manager.add_mcp_server(
        name="calculator",
        command="python",
        args=[os.path.join(os.path.dirname(__file__), "..", "mcps", "demo_calculator.py")],
        env={}
    )
    
    if calculator_success:
        print("✅ Calculator MCP server added successfully")
    else:
        print("❌ Failed to add calculator MCP server")
        print("   (This is expected if the server file doesn't exist)")
    
    # Check server health
    server_health = await tool_manager.get_mcp_server_status()
    print(f"🏥 Server health status: {server_health}")
    
    # List all tools after MCP integration
    tools_info = await tool_manager.list_all_tools()
    print(f"📋 Updated tool summary:")
    print(f"   Local tools: {len(tools_info['local_tools'])}")
    print(f"   MCP tools: {len(tools_info['mcp_tools'])}")
    print(f"   MCP servers: {len(tools_info['mcp_servers'])}")
    print(f"   Total schemas: {tools_info['total_schemas']}")
    
    if tools_info['mcp_tools']:
        print("🔧 Available MCP tools:")
        for tool in tools_info['mcp_tools']:
            print(f"   - {tool['mcp_name']}:{tool['tool_name']}: {tool['description']}")
    
    print("✅ Demo 2 completed!\n")


async def demo_factory_function():
    """Demonstrate using the factory function."""
    print("🏭 Demo 3: Factory Function Usage")
    print("=" * 50)
    
    # Create server configurations
    servers = [
        MCPServerConfig(
            name="demo_calculator",
            command="python",
            args=[os.path.join(os.path.dirname(__file__), "..", "mcps", "demo_calculator.py")],
            env={}
        )
    ]
    
    # Create tool manager with servers
    chat_history = SimpleChatHistory()
    
    try:
        tool_manager = await create_enhanced_tool_manager_with_servers(
            chat_history=chat_history,
            mcp_servers=servers
        )
        
        print("✅ Created tool manager with factory function")
        
        # Add local tools
        tool_manager.register_tool(get_current_time)
        
        # Get tool information
        tools_info = await tool_manager.list_all_tools()
        print(f"📋 Factory-created manager:")
        print(f"   Local tools: {len(tools_info['local_tools'])}")
        print(f"   MCP tools: {len(tools_info['mcp_tools'])}")
        print(f"   Total schemas: {tools_info['total_schemas']}")
        
        # Test tool execution
        if tools_info['local_tools']:
            tool_call = ToolCall(
                id="demo_3",
                name="get_current_time",
                arguments='{}'
            )
            
            result = await tool_manager.execute_tool_call(tool_call)
            print(f"🕒 Current time: {result}")
        
        # Cleanup
        await tool_manager.cleanup()
        print("✅ Demo 3 completed successfully!\n")
        
    except Exception as e:
        print(f"⚠️  Demo 3 encountered an issue: {e}")
        print("   This is normal if MCP dependencies aren't fully set up\n")


async def demo_tool_execution_flow():
    """Demonstrate the tool execution flow."""
    print("⚡ Demo 4: Tool Execution Flow")
    print("=" * 50)
    
    # Create simple tool manager
    chat_history = SimpleChatHistory()
    tool_manager = EnhancedToolManager(chat_history)
    
    # Register tools
    tool_manager.register_tool(reverse_string)
    tool_manager.register_tool(count_words)
    
    # Test different tool calls
    test_calls = [
        ToolCall(id="test_1", name="reverse_string", arguments='{"text": "MCP is awesome!"}'),
        ToolCall(id="test_2", name="count_words", arguments='{"text": "The quick brown fox jumps"}'),
        ToolCall(id="test_3", name="nonexistent_tool", arguments='{}'),  # This should fail gracefully
    ]
    
    print("🔧 Testing tool execution flow:")
    
    for i, tool_call in enumerate(test_calls, 1):
        print(f"   Test {i}: {tool_call.name}")
        
        # Check tool type
        if tool_manager.is_local_tool(tool_call.name):
            print(f"      → Identified as local tool")
        elif tool_manager.is_mcp_tool(tool_call.name):
            print(f"      → Identified as MCP tool")
        else:
            print(f"      → Tool not found")
        
        # Execute tool
        result = await tool_manager.execute_tool_call(tool_call)
        print(f"      → Result: {result}")
    
    print("✅ Demo 4 completed!\n")


async def demo_error_handling():
    """Demonstrate error handling capabilities."""
    print("🛡️  Demo 5: Error Handling")
    print("=" * 50)
    
    chat_history = SimpleChatHistory()
    tool_manager = EnhancedToolManager(chat_history)
    
    # Register a tool that can fail
    def divide_numbers(a: float, b: float) -> float:
        """Divide two numbers."""
        if b == 0:
            raise ValueError("Cannot divide by zero")
        return a / b
    
    tool_manager.register_tool(divide_numbers)
    
    # Test error scenarios
    error_tests = [
        ("Valid division", '{"a": 10, "b": 2}'),
        ("Division by zero", '{"a": 10, "b": 0}'),
        ("Invalid arguments", '{"a": "not_a_number", "b": 2}'),
        ("Missing arguments", '{"a": 10}'),
    ]
    
    print("🧪 Testing error handling:")
    
    for test_name, arguments in error_tests:
        print(f"   {test_name}:")
        
        tool_call = ToolCall(
            id="error_test",
            name="divide_numbers",
            arguments=arguments
        )
        
        result = await tool_manager.execute_tool_call(tool_call)
        print(f"      → {result}")
    
    print("✅ Demo 5 completed!\n")


async def main():
    """Run all demos."""
    print("🎯 MCP Integration Demo")
    print("=" * 60)
    print("This demo showcases the MCP integration with LLMgine")
    print("=" * 60)
    print()
    
    try:
        # Demo 1: Basic setup
        tool_manager = await demo_basic_setup()
        
        # Demo 2: MCP integration
        await demo_mcp_integration(tool_manager)
        
        # Demo 3: Factory function
        await demo_factory_function()
        
        # Demo 4: Tool execution flow
        await demo_tool_execution_flow()
        
        # Demo 5: Error handling
        await demo_error_handling()
        
        # Cleanup
        await tool_manager.cleanup()
        
        print("🎉 All demos completed successfully!")
        print("=" * 60)
        print("Key takeaways:")
        print("✅ Enhanced ToolManager maintains backward compatibility")
        print("✅ MCP servers can be easily integrated")
        print("✅ Unified interface for local and MCP tools")
        print("✅ Robust error handling and monitoring")
        print("✅ Factory functions simplify setup")
        
    except Exception as e:
        print(f"💥 Demo failed with error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())

