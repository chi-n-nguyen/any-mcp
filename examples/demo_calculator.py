#!/usr/bin/env python3
"""
Simple Calculator MCP Server - Demo for any-mcp

A basic calculator that demonstrates MCP server functionality without external dependencies.
Perfect for testing the any-mcp CLI!

Usage:
    python mcps/demo_calculator.py
    
Test with CLI:
    uv run python -m any_mcp.cli.main call --script mcps/demo_calculator.py --tool add --args a=5,b=3
"""

import asyncio
import json
import sys
from typing import Any, Dict, List, Optional


class CalculatorMCPServer:
    """Simple calculator MCP server for demo purposes"""
    
    def __init__(self):
        self.tools = [
            {
                "name": "add",
                "description": "Add two numbers together",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "a": {"type": "number", "description": "First number"},
                        "b": {"type": "number", "description": "Second number"}
                    },
                    "required": ["a", "b"]
                }
            },
            {
                "name": "subtract", 
                "description": "Subtract second number from first",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "a": {"type": "number", "description": "First number"},
                        "b": {"type": "number", "description": "Second number"}
                    },
                    "required": ["a", "b"]
                }
            },
            {
                "name": "multiply",
                "description": "Multiply two numbers",
                "inputSchema": {
                    "type": "object", 
                    "properties": {
                        "a": {"type": "number", "description": "First number"},
                        "b": {"type": "number", "description": "Second number"}
                    },
                    "required": ["a", "b"]
                }
            },
            {
                "name": "divide",
                "description": "Divide first number by second",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "a": {"type": "number", "description": "Dividend (number to be divided)"},
                        "b": {"type": "number", "description": "Divisor (number to divide by, cannot be zero)"}
                    },
                    "required": ["a", "b"]
                }
            },
            {
                "name": "power",
                "description": "Raise first number to the power of second number", 
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "base": {"type": "number", "description": "Base number"},
                        "exponent": {"type": "number", "description": "Exponent"}
                    },
                    "required": ["base", "exponent"]
                }
            }
        ]

    async def handle_initialize(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle MCP initialize request"""
        return {
            "protocolVersion": "2024-11-05",
            "capabilities": {
                "tools": {}
            },
            "serverInfo": {
                "name": "demo-calculator",
                "version": "1.0.0"
            }
        }

    async def handle_list_tools(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle MCP list tools request"""
        return {
            "tools": self.tools
        }

    async def handle_call_tool(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle MCP call tool request"""
        tool_name = params.get("name")
        arguments = params.get("arguments", {})
        
        try:
            if tool_name == "add":
                a = float(arguments["a"])
                b = float(arguments["b"])
                result = a + b
                return {
                    "content": [
                        {
                            "type": "text",
                            "text": f"✅ {a} + {b} = {result}"
                        }
                    ]
                }
                
            elif tool_name == "subtract":
                a = float(arguments["a"])
                b = float(arguments["b"])
                result = a - b
                return {
                    "content": [
                        {
                            "type": "text", 
                            "text": f"✅ {a} - {b} = {result}"
                        }
                    ]
                }
                
            elif tool_name == "multiply":
                a = float(arguments["a"])
                b = float(arguments["b"])
                result = a * b
                return {
                    "content": [
                        {
                            "type": "text",
                            "text": f"✅ {a} × {b} = {result}"
                        }
                    ]
                }
                
            elif tool_name == "divide":
                a = float(arguments["a"])
                b = float(arguments["b"])
                if b == 0:
                    return {
                        "content": [
                            {
                                "type": "text",
                                "text": "❌ Error: Cannot divide by zero!"
                            }
                        ],
                        "isError": True
                    }
                result = a / b
                return {
                    "content": [
                        {
                            "type": "text",
                            "text": f"✅ {a} ÷ {b} = {result}"
                        }
                    ]
                }
                
            elif tool_name == "power":
                base = float(arguments["base"])
                exponent = float(arguments["exponent"])
                result = base ** exponent
                return {
                    "content": [
                        {
                            "type": "text",
                            "text": f"✅ {base}^{exponent} = {result}"
                        }
                    ]
                }
                
            else:
                return {
                    "content": [
                        {
                            "type": "text",
                            "text": f"❌ Unknown tool: {tool_name}"
                        }
                    ],
                    "isError": True
                }
                
        except (KeyError, ValueError, TypeError) as e:
            return {
                "content": [
                    {
                        "type": "text",
                        "text": f"❌ Error: Invalid arguments - {str(e)}"
                    }
                ],
                "isError": True
            }

    async def handle_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Handle incoming MCP request"""
        method = request.get("method")
        params = request.get("params", {})
        
        if method == "initialize":
            result = await self.handle_initialize(params)
        elif method == "tools/list":
            result = await self.handle_list_tools(params)
        elif method == "tools/call":
            result = await self.handle_call_tool(params)
        else:
            result = {
                "error": {
                    "code": -32601,
                    "message": f"Method not found: {method}"
                }
            }
        
        return {
            "jsonrpc": "2.0",
            "id": request.get("id"),
            "result": result
        }

    async def run(self):
        """Run the MCP server"""
        print("🧮 Demo Calculator MCP Server starting...", file=sys.stderr)
        print("🔧 Available tools: add, subtract, multiply, divide, power", file=sys.stderr)
        
        while True:
            try:
                line = await asyncio.get_event_loop().run_in_executor(None, sys.stdin.readline)
                if not line:
                    break
                    
                line = line.strip()
                if not line:
                    continue
                    
                try:
                    request = json.loads(line)
                    response = await self.handle_request(request)
                    print(json.dumps(response))
                    sys.stdout.flush()
                except json.JSONDecodeError:
                    print("❌ Invalid JSON request", file=sys.stderr)
                    
            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"❌ Server error: {e}", file=sys.stderr)
        
        print("👋 Calculator MCP Server stopped", file=sys.stderr)


async def main():
    """Main entry point"""
    server = CalculatorMCPServer()
    await server.run()


if __name__ == "__main__":
    asyncio.run(main())
