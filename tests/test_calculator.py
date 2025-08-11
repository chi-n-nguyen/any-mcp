#!/usr/bin/env python3
"""
Simple test script to demonstrate calculator MCP usage
"""

import asyncio
import sys
from contextlib import AsyncExitStack
from mcp_client import MCPClient

async def test_calculator():
    """Simple test of calculator MCP"""
    
    async with AsyncExitStack() as stack:
        # Connect to calculator
        client = await stack.enter_async_context(
            MCPClient(command="uv", args=["run", "demos/mcp_calc_server.py"])
        )
        
        print("✅ Connected to calculator!")
        
        # List available tools
        tools = await client.list_tools()
        print(f"\n🔧 Available tools: {[tool.name for tool in tools]}")
        
        # Test some calculations
        print("\n🧮 Testing calculations:")
        
        # Add
        result = await client.call_tool("add", {"a": 15, "b": 25})
        print(f"15 + 25 = {result.content[0].text if result and result.content else 'Error'}")
        
        # Multiply  
        result = await client.call_tool("multiply", {"a": 7, "b": 8})
        print(f"7 × 8 = {result.content[0].text if result and result.content else 'Error'}")
        
        # Power
        result = await client.call_tool("power", {"base": 2, "exponent": 10})
        print(f"2^10 = {result.content[0].text if result and result.content else 'Error'}")
        
        # Interactive mode
        print("\n💬 Interactive mode - Type calculations or 'quit' to exit:")
        print("Examples: add 5 10, multiply 3 7, power 2 8, divide 20 4")
        
        while True:
            try:
                user_input = input("\n> ").strip()
                
                if user_input.lower() in ['quit', 'exit', 'q']:
                    break
                
                if not user_input:
                    continue
                
                # Parse simple commands like "add 5 10"
                parts = user_input.split()
                if len(parts) >= 3:
                    tool_name = parts[0].lower()
                    try:
                        if tool_name in ['add', 'subtract', 'multiply', 'divide']:
                            a, b = float(parts[1]), float(parts[2])
                            result = await client.call_tool(tool_name, {"a": a, "b": b})
                        elif tool_name == 'power':
                            base, exp = float(parts[1]), float(parts[2])
                            result = await client.call_tool("power", {"base": base, "exponent": exp})
                        else:
                            print(f"❌ Unknown tool: {tool_name}")
                            print("Available tools: add, subtract, multiply, divide, power")
                            continue
                        
                        if result and result.content:
                            print(f"Result: {result.content[0].text}")
                        else:
                            print("❌ Calculation failed")
                            
                    except ValueError:
                        print("❌ Invalid numbers. Use format: <tool> <num1> <num2>")
                    except Exception as e:
                        print(f"❌ Error: {e}")
                else:
                    print("❌ Format: <tool> <num1> <num2>")
                    print("Example: add 5 10")
                    
            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"❌ Error: {e}")
        
        print("\n👋 Goodbye!")

if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    
    asyncio.run(test_calculator())