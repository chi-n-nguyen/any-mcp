#!/usr/bin/env python3
"""
Demo Calculator MCP Server

A simple MCP server that provides basic mathematical operations.
This demonstrates how to create an MCP server for the llmgine integration.
"""

import asyncio
import json
import sys
from typing import Any, Dict

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent, CallToolResult


# Create the MCP server
app = Server("demo-calculator")


@app.list_tools()
async def list_tools() -> list[Tool]:
    """List available calculator tools."""
    return [
        Tool(
            name="add",
            description="Add two numbers",
            inputSchema={
                "type": "object",
                "properties": {
                    "a": {"type": "number", "description": "First number"},
                    "b": {"type": "number", "description": "Second number"}
                },
                "required": ["a", "b"]
            }
        ),
        Tool(
            name="subtract",
            description="Subtract two numbers",
            inputSchema={
                "type": "object",
                "properties": {
                    "a": {"type": "number", "description": "First number"},
                    "b": {"type": "number", "description": "Second number"}
                },
                "required": ["a", "b"]
            }
        ),
        Tool(
            name="multiply",
            description="Multiply two numbers",
            inputSchema={
                "type": "object",
                "properties": {
                    "a": {"type": "number", "description": "First number"},
                    "b": {"type": "number", "description": "Second number"}
                },
                "required": ["a", "b"]
            }
        ),
        Tool(
            name="divide",
            description="Divide two numbers",
            inputSchema={
                "type": "object",
                "properties": {
                    "a": {"type": "number", "description": "Dividend"},
                    "b": {"type": "number", "description": "Divisor"}
                },
                "required": ["a", "b"]
            }
        ),
        Tool(
            name="power",
            description="Raise a number to a power",
            inputSchema={
                "type": "object",
                "properties": {
                    "base": {"type": "number", "description": "Base number"},
                    "exponent": {"type": "number", "description": "Exponent"}
                },
                "required": ["base", "exponent"]
            }
        ),
        Tool(
            name="sqrt",
            description="Calculate square root of a number",
            inputSchema={
                "type": "object",
                "properties": {
                    "number": {"type": "number", "description": "Number to calculate square root of"}
                },
                "required": ["number"]
            }
        )
    ]


@app.call_tool()
async def call_tool(name: str, arguments: Dict[str, Any]) -> CallToolResult:
    """Handle tool calls."""
    try:
        if name == "add":
            result = arguments["a"] + arguments["b"]
            return CallToolResult(
                content=[TextContent(type="text", text=str(result))]
            )
        
        elif name == "subtract":
            result = arguments["a"] - arguments["b"]
            return CallToolResult(
                content=[TextContent(type="text", text=str(result))]
            )
        
        elif name == "multiply":
            result = arguments["a"] * arguments["b"]
            return CallToolResult(
                content=[TextContent(type="text", text=str(result))]
            )
        
        elif name == "divide":
            if arguments["b"] == 0:
                return CallToolResult(
                    content=[TextContent(type="text", text="Error: Division by zero")],
                    isError=True
                )
            result = arguments["a"] / arguments["b"]
            return CallToolResult(
                content=[TextContent(type="text", text=str(result))]
            )
        
        elif name == "power":
            result = arguments["base"] ** arguments["exponent"]
            return CallToolResult(
                content=[TextContent(type="text", text=str(result))]
            )
        
        elif name == "sqrt":
            if arguments["number"] < 0:
                return CallToolResult(
                    content=[TextContent(type="text", text="Error: Cannot calculate square root of negative number")],
                    isError=True
                )
            result = arguments["number"] ** 0.5
            return CallToolResult(
                content=[TextContent(type="text", text=str(result))]
            )
        
        else:
            return CallToolResult(
                content=[TextContent(type="text", text=f"Error: Unknown tool '{name}'")],
                isError=True
            )
    
    except Exception as e:
        return CallToolResult(
            content=[TextContent(type="text", text=f"Error: {str(e)}")],
            isError=True
        )


async def main():
    """Run the MCP server."""
    async with stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            app.create_initialization_options()
        )


if __name__ == "__main__":
    asyncio.run(main())

