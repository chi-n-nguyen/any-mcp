#!/usr/bin/env python3
"""
Demo script showing any-mcp working with mcp-calc.
"""

import asyncio
import sys
from pathlib import Path

# Add the src directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from any_mcp import AnyMCP


async def main():
    """Demo the any-mcp adapter with the calculator MCP."""
    
    # Path to our calculator MCP
    calc_mcp_path = Path(__file__).parent / "mcp_calc_server.py"
    
    print("Starting any-mcp demo with calculator MCP...")
    print(f"MCP Path: {calc_mcp_path}")
    print()
    
    async with AnyMCP(str(calc_mcp_path)) as calc:
        # Discover available tools
        tools = calc.list_tools()
        print(f"Discovered tools: {tools}")
        print()
        
        # Demo some calculations
        print("Running calculations...")
        
        # Addition
        result = await calc.call_tool("add", a=5, b=3)
        print(f"5 + 3 = {result}")
        
        # Multiplication
        result = await calc.call_tool("multiply", a=4, b=7)
        print(f"4 × 7 = {result}")
        
        # Power
        result = await calc.call_tool("power", base=2, exponent=8)
        print(f"2^8 = {result}")
        
        # Division
        result = await calc.call_tool("divide", a=15, b=3)
        print(f"15 ÷ 3 = {result}")
        
        print()
        print("Demo completed successfully!")
        print("any-mcp successfully started the MCP, discovered tools, and executed calculations!")


if __name__ == "__main__":
    asyncio.run(main()) 