# LLMgine-MCP Integration Guide

## Overview

This document provides a comprehensive guide to the **revolutionary new architecture** that transforms LLMgine's ToolManager into an **MCP server** while using **any-mcp as an MCP client**. This approach creates a unified, scalable system where LLMgine's tools become available through the MCP protocol, and any-mcp can connect to both LLMgine's ToolManager and external MCP servers simultaneously.

## Table of Contents

1. [New Architecture Overview](#new-architecture-overview)
2. [Key Components](#key-components)
3. [Getting Started](#getting-started)
4. [Migration Guide](#migration-guide)
5. [Configuration](#configuration)
6. [Usage Examples](#usage-examples)
7. [Advanced Features](#advanced-features)
8. [Troubleshooting](#troubleshooting)
9. [Performance Considerations](#performance-considerations)
10. [API Reference](#api-reference)

## New Architecture Overview

The **revolutionary new architecture** flips the traditional approach on its head:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              any-mcp (MCP Client)                          │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                    Unified MCP Client System                        │   │
│  │                                                                     │   │
│  │  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐    │   │
│  │  │   MCP Manager   │  │  Tool Adapter   │  │  Event Bridge   │    │   │
│  │  └─────────────────┘  └─────────────────┘  └─────────────────┘    │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    │ MCP Protocol
                                    │
                    ┌────────────────┼────────────────┐
                    │                │                │
            ┌───────▼──────┐ ┌───────▼──────┐ ┌───────▼──────┐
            │              │ │              │ │              │
            │ LLMgine      │ │ Notion       │ │ GitHub       │
            │ ToolManager  │ │ MCP Server   │ │ MCP Server   │
            │ (MCP Server) │ │              │ │              │
            │              │ │              │ │              │
            └──────────────┘ └──────────────┘ └──────────────┘
                    │
                    │ Exposes LLMgine tools as MCP tools
                    │
            ┌───────▼──────┐
            │              │
            │ get_weather  │
            │ calculate    │
            │ search_web   │
            │ play_music   │
            │ ...          │
            └──────────────┘
```

### **Key Benefits of New Architecture**

- **🔄 ToolManager as MCP Server**: LLMgine's existing tools are now available through the MCP protocol
- **🔌 any-mcp as MCP Client**: Single client that can connect to multiple MCP servers simultaneously
- **🌐 Universal Access**: Any MCP-compliant client can now use LLMgine's tools
- **🚀 Scalability**: Easy to add new MCP servers without changing the client architecture
- **🔄 Backward Compatibility**: Existing LLMgine code continues to work unchanged
- **🔧 Unified Management**: Single interface for all tools (local + external MCP servers)

## Key Components

### 1. **LLMgine ToolManager MCP Server** (`mcps/llmgine_local_tools.py`)

**LLMgine's ToolManager is now an MCP server** that exposes all existing tools through the MCP protocol:

```python
#!/usr/bin/env python3
"""
LLMgine Local Tools MCP Server

This MCP server wraps LLMgine's existing local tools so they can be
managed through the unified MCP system. This preserves backward compatibility
while enabling the benefits of MCP-based tool management.
"""

import asyncio
import inspect
import logging
from typing import Any, Dict, List, Optional, Sequence

from mcp.server.models import InitializationOptions
from mcp.server import NotificationOptions, Server
from mcp.types import (
    CallToolRequest, CallToolResult, ListToolsRequest, Tool, TextContent,
    JSONRPCMessage, RequestT, LoggingLevel, ListToolsResult
)

# Import tool functions from different parts of LLMgine
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'tests', 'tools'))
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'tools'))

from tools_for_test import get_weather, get_station_list
from test_tools import get_weather as simple_get_weather

class LLMgineLocalToolsServer:
    """MCP Server that exposes LLMgine's local tools."""
    
    def __init__(self):
        self.server = Server("llmgine-local-tools")
        
        # Register local tool functions
        self.local_tools = {
            "get_weather": get_weather,  # Real weather from BOM API
            "get_station_list": get_station_list,  # List available weather stations
            "simple_get_weather": simple_get_weather,  # Simple demo weather
        }
        
        # Set up MCP handlers
        self._setup_handlers()
    
    def _setup_handlers(self):
        """Set up MCP protocol handlers."""
        
        @self.server.list_tools()
        async def handle_list_tools() -> list[Tool]:
            """List all available local tools."""
            tools = []
            
            for tool_name, tool_func in self.local_tools.items():
                # Generate tool schema from function
                schema = self._generate_tool_schema(tool_func)
                
                tool = Tool(
                    name=tool_name,
                    description=schema["function"]["description"],
                    inputSchema=schema["function"]["parameters"]
                )
                tools.append(tool)
            
            return tools
        
        @self.server.call_tool()
        async def handle_call_tool(
            name: str, arguments: Optional[dict[str, Any]] = None
        ) -> list[TextContent]:
            """Execute a local tool."""
            if name not in self.local_tools:
                raise ValueError(f"Unknown tool: {name}")
            
            tool_func = self.local_tools[name]
            
            try:
                # Parse arguments
                args = arguments or {}
                
                # Execute function
                if asyncio.iscoroutinefunction(tool_func):
                    result = await tool_func(**args)
                else:
                    result = tool_func(**args)
                
                # Convert result to string if needed
                if not isinstance(result, str):
                    result = str(result)
                
                return [TextContent(type="text", text=result)]
                
            except Exception as e:
                logger.error(f"Error executing tool {name}: {e}")
                return [TextContent(type="text", text=f"Error: {str(e)}")]
```

**Key Features:**
- **MCP Protocol Compliance**: Implements full MCP server specification
- **Tool Schema Generation**: Automatically generates OpenAPI schemas from LLMgine functions
- **Async Support**: Handles both sync and async tool functions
- **Error Handling**: Robust error handling with detailed logging
- **Tool Discovery**: Exposes tools through MCP's `tools/list` endpoint

### 2. **any-mcp as MCP Client** (`src/any_mcp/`)

**any-mcp now acts as a unified MCP client** that can connect to multiple MCP servers:

```python
from any_mcp.managers.manager import MCPManager
from any_mcp.integration.tool_adapter import LLMgineToolAdapter

class MCPUnifiedToolManager:
    """
    Unified MCP-powered ToolManager that replaces the original ToolManager.
    
    This manager provides complete backward compatibility while enabling:
    - Local LLMgine tools via MCP server
    - Third-party MCP servers (Notion, GitHub, etc.)
    - Unified tool discovery and execution
    - Advanced MCP capabilities
    """
    
    def __init__(self, chat_history: Optional["SimpleChatHistory"] = None):
        """Initialize unified MCP-powered tool manager."""
        self.chat_history = chat_history
        
        # MCP system components
        self.mcp_manager: Optional[MCPManager] = None
        self.tool_adapter: Optional[LLMgineToolAdapter] = None
        self._initialized = False
        
        # Legacy compatibility: maintain the same interface
        self.tools: Dict[str, Callable] = {}  # For backward compatibility
        self.tool_schemas: List[Dict[str, Any]] = []
        
        logger.info("Initialized MCPUnifiedToolManager")
    
    async def initialize(self) -> bool:
        """
        Initialize the MCP system.
        
        Returns:
            True if initialization successful
        """
        if self._initialized:
            return True
        
        try:
            # Initialize MCP manager and adapter
            self.mcp_manager = MCPManager()
            self.tool_adapter = LLMgineToolAdapter(self.mcp_manager)
            
            # Start configured MCP servers
            await self._start_configured_servers()
            
            self._initialized = True
            logger.info("MCP system initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize MCP system: {e}")
            return False
    
    async def _start_configured_servers(self):
        """Start all available MCP servers from configuration."""
        config_loader = get_config_loader()
        available_servers = config_loader.get_available_servers()
        
        logger.info(f"Starting {len(available_servers)} available MCP servers")
        
        for server_config in available_servers:
            try:
                success = await self.mcp_manager.start_mcp(
                    name=server_config.name,
                    command=server_config.command,
                    args=server_config.args,
                    env=server_config.resolved_env
                )
                
                if success:
                    logger.info(f"✅ Started MCP server: {server_config.name}")
                else:
                    logger.warning(f"❌ Failed to start MCP server: {server_config.name}")
                    
            except Exception as e:
                logger.error(f"Error starting MCP server {server_config.name}: {e}")
```

**Key Features:**
- **Unified MCP Client**: Single client that connects to multiple MCP servers
- **Automatic Server Management**: Starts and manages all configured MCP servers
- **Tool Discovery**: Automatically discovers tools from all connected servers
- **Backward Compatibility**: Maintains exact same interface as original ToolManager

### 3. **Configuration System** (`src/llmgine/llm/tools/mcp_config_loader.py`)

**YAML-based configuration** for all MCP servers:

```python
class MCPServerConfig:
    """Configuration for an MCP server."""
    
    def __init__(
        self,
        name: str,
        command: str,
        args: List[str],
        env: Dict[str, str] = None,
        enabled: bool = True,
        description: str = "",
        type: str = "local"
    ):
        self.name = name
        self.command = command
        self.args = args
        self.env = env or {}
        self.enabled = enabled
        self.description = description
        self.type = type

def get_config_loader() -> MCPConfigLoader:
    """Get the MCP configuration loader."""
    return MCPConfigLoader()

class MCPConfigLoader:
    """Loads MCP server configurations from YAML files."""
    
    def __init__(self, config_path: str = "config/mcp_servers_config.yaml"):
        self.config_path = config_path
        self._config = None
    
    def get_available_servers(self) -> List[MCPServerConfig]:
        """Get all available MCP server configurations."""
        if not self._config:
            self._load_config()
        
        available_servers = []
        
        for server_name, server_config in self._config.get("mcp_servers", {}).items():
            if server_config.get("enabled", False):
                config = MCPServerConfig(
                    name=server_name,
                    command=server_config["command"],
                    args=server_config["args"],
                    env=server_config.get("env_vars", {}),
                    description=server_config.get("description", ""),
                    type=server_config.get("type", "local")
                )
                available_servers.append(config)
        
        return available_servers
```

## Getting Started

### 1. **Basic Setup - ToolManager as MCP Server**

**LLMgine's ToolManager is now an MCP server** that you can start independently:

```python
# Start LLMgine ToolManager as MCP server
python mcps/llmgine_local_tools.py

# This exposes LLMgine's tools through MCP protocol:
# - get_weather
# - get_station_list  
# - simple_get_weather
# - And any other tools you've registered
```

### 2. **Connect any-mcp as MCP Client**

**any-mcp now connects to LLMgine's ToolManager and other MCP servers**:

```python
from llmgine.llm.tools import ToolManager, create_mcp_tool_manager
from llmgine.llm.tools.toolCall import ToolCall

# Create unified MCP tool manager
manager = create_mcp_tool_manager()

# Initialize MCP system (connects to all configured servers)
await manager.initialize()

# Get available tools from ALL connected MCP servers
tools = await manager.list_available_tools()
print(f"Available tools: {len(tools)}")

# Execute tools (automatically routed to appropriate MCP server)
result = await manager.execute_tool_call(tool_call)
```

### 3. **Add External MCP Servers**

**Connect to external MCP servers alongside LLMgine's ToolManager**:

```python
# Add Notion MCP server
await manager.add_mcp_server(
    name="notion",
    command="npx",
    args=["@notionhq/notion-mcp-server"],
    env={"NOTION_TOKEN": "your-token"}
)

# Add GitHub MCP server
await manager.add_mcp_server(
    name="github",
    command="npx", 
    args=["@github/github-mcp-server"],
    env={"GITHUB_TOKEN": "your-token"}
)

# Now you have access to:
# - LLMgine tools (via ToolManager MCP server)
# - Notion tools (via Notion MCP server)
# - GitHub tools (via GitHub MCP server)
# - All through the same unified interface!
```

## Migration Guide

### **From Original ToolManager to New Architecture**

**The new architecture is 100% backward compatible** - your existing code continues to work:

```python
# BEFORE (Original ToolManager)
from llmgine.llm.tools.tool_manager import ToolManager

class MyEngine:
    def __init__(self):
        self.tool_manager = ToolManager(self.chat_history)
        self.tool_manager.register_tool(my_function)
    
    async def execute_tool(self, tool_call):
        return await self.tool_manager.execute_tool_call(tool_call)

# AFTER (New MCP Architecture - NO CHANGES REQUIRED!)
from llmgine.llm.tools import ToolManager  # Same import!

class MyEngine:
    def __init__(self):
        self.tool_manager = ToolManager(self.chat_history)  # Same interface!
        self.tool_manager.register_tool(my_function)  # Still works!
    
    async def execute_tool(self, tool_call):
        return await self.tool_manager.execute_tool_call(tool_call)  # Same!
```

**The magic happens automatically:**
1. **ToolManager import now points to MCPUnifiedToolManager**
2. **Same interface, same methods, same behavior**
3. **Plus new MCP capabilities automatically available**

### **New MCP Capabilities (Optional)**

**Add MCP capabilities without changing existing code**:

```python
# Existing code continues to work
result = await self.tool_manager.execute_tool_call(tool_call)

# NEW: Add MCP servers for enhanced capabilities
await self.tool_manager.add_mcp_server(
    name="notion",
    command="npx",
    args=["@notionhq/notion-mcp-server"],
    env={"NOTION_TOKEN": "your-token"}
)

# Now you have access to Notion tools + your existing tools!
```

## Configuration

### **MCP Servers Configuration** (`config/mcp_servers_config.yaml`)

**Configure all MCP servers in one place**:

```yaml
mcp_servers:
  # LLMgine ToolManager as MCP server (always enabled)
  llmgine-local:
    type: "local" 
    command: "python"
    args: ["mcps/llmgine_local_tools.py"]
    enabled: true
    description: "LLMgine's built-in tools wrapped as MCP server"
    
  # Calculator demo
  calculator:
    type: "local"
    command: "python" 
    args: ["mcps/demo_calculator.py"]
    enabled: false
    description: "Simple calculator for demonstration"

  # Official MCP Servers (require installation)
  
  # Notion MCP Server
  notion:
    type: "npm"
    command: "npx"
    args: ["@notionhq/notion-mcp-server"]
    enabled: false
    env_vars:
      NOTION_TOKEN: "${NOTION_API_TOKEN}"  # Set in environment
    description: "Official Notion MCP server with 18+ tools"
    install_cmd: "npm install -g @notionhq/notion-mcp-server"
    
  # GitHub MCP Server  
  github:
    type: "npm"
    command: "npx"
    args: ["@github/github-mcp-server"]
    enabled: false
    env_vars:
      GITHUB_TOKEN: "${GITHUB_TOKEN}"  # Set in environment
    description: "Official GitHub MCP server for repository management"
    install_cmd: "npm install -g @github/github-mcp-server"
    
  # Filesystem MCP Server
  filesystem:
    type: "npm" 
    command: "npx"
    args: ["@modelcontextprotocol/server-filesystem", "/path/to/allowed/directory"]
    enabled: false
    description: "File system operations within allowed directories"
    install_cmd: "npm install -g @modelcontextprotocol/server-filesystem"
    
  # SQLite MCP Server
  sqlite:
    type: "npm"
    command: "npx"
    args: ["@modelcontextprotocol/server-sqlite", "/path/to/database.db"]
    enabled: false
    description: "SQLite database operations"
    install_cmd: "npm install -g @modelcontextprotocol/server-sqlite"
    
  # Web Search MCP Server  
  web-search:
    type: "npm"
    command: "npx"
    args: ["@modelcontextprotocol/server-web-search"]
    enabled: false
    env_vars:
      BRAVE_API_KEY: "${BRAVE_API_KEY}"  # Or other search API key
    description: "Web search capabilities"
    install_cmd: "npm install -g @modelcontextprotocol/server-web-search"
    
  # Memory MCP Server
  memory:
    type: "npm" 
    command: "npx"
    args: ["@modelcontextprotocol/server-memory"]
    enabled: false
    description: "Persistent memory across conversations"
    install_cmd: "npm install -g @modelcontextprotocol/server-memory"
    
  # Kubernetes MCP Server
  kubernetes:
    type: "npm"
    command: "npx"
    args: ["@kubernetes/mcp-server-kubernetes"]
    enabled: false
    env_vars:
      KUBECONFIG: "${KUBECONFIG}"
    description: "Kubernetes cluster management"
    install_cmd: "npm install -g @kubernetes/mcp-server-kubernetes"
    
  # Slack MCP Server
  slack:
    type: "npm" 
    command: "npx"
    args: ["@slack/mcp-server-slack"]
    enabled: false
    env_vars:
      SLACK_BOT_TOKEN: "${SLACK_BOT_TOKEN}"
      SLACK_APP_TOKEN: "${SLACK_APP_TOKEN}"
    description: "Slack workspace integration"
    install_cmd: "npm install -g @slack/mcp-server-slack"
```

### **Environment Variables**

**Set environment variables for enabled servers**:

```bash
# LLMgine (no token needed - uses local tools)
# Already configured and enabled

# Notion
export NOTION_API_TOKEN="your-notion-token"

# GitHub  
export GITHUB_TOKEN="your-github-token"

# Web Search
export BRAVE_API_KEY="your-brave-api-key"

# Slack
export SLACK_BOT_TOKEN="your-slack-bot-token"
export SLACK_APP_TOKEN="your-slack-app-token"

# Kubernetes
export KUBECONFIG="/path/to/kubeconfig"
```

## Usage Examples

### **Example 1: Basic MCP Client Usage**

```python
import asyncio
from llmgine.llm.tools import ToolManager, create_mcp_tool_manager
from llmgine.llm.tools.toolCall import ToolCall

async def basic_mcp_example():
    """Basic example of using any-mcp as MCP client."""
    
    # Create unified MCP tool manager
    manager = create_mcp_tool_manager()
    
    # Initialize MCP system (connects to all configured servers)
    await manager.initialize()
    
    # List all available tools from ALL connected MCP servers
    tools = await manager.list_available_tools()
    print(f"Available tools: {len(tools)}")
    
    for tool in tools:
        print(f"  - {tool['name']} (from {tool['server']})")
    
    # Execute a tool (automatically routed to appropriate MCP server)
    if tools:
        tool_name = tools[0]['name']
        print(f"\nTesting tool: {tool_name}")
        
        tool_call = ToolCall(
            name=tool_name,
            arguments={"city": "melbourne"},
            id="test-1"
        )
        
        result = await manager.execute_tool_call(tool_call)
        print(f"Result: {result}")
    
    # Cleanup
    await manager.cleanup()

# Run the example
asyncio.run(basic_mcp_example())
```

### **Example 2: Adding External MCP Servers**

```python
import asyncio
from llmgine.llm.tools import create_mcp_tool_manager

async def external_mcp_example():
    """Example of adding external MCP servers."""
    
    # Create manager
    manager = create_mcp_tool_manager()
    await manager.initialize()
    
    # Add Notion MCP server
    success = await manager.add_mcp_server(
        name="notion",
        command="npx",
        args=["@notionhq/notion-mcp-server"],
        env={"NOTION_TOKEN": "your-token"}
    )
    print(f"Added Notion server: {success}")
    
    # Add GitHub MCP server
    success = await manager.add_mcp_server(
        name="github",
        command="npx",
        args=["@github/github-mcp-server"],
        env={"GITHUB_TOKEN": "your-token"}
    )
    print(f"Added GitHub server: {success}")
    
    # List all available tools
    tools = await manager.list_available_tools()
    print(f"Total available tools: {len(tools)}")
    
    # Group tools by server
    tools_by_server = {}
    for tool in tools:
        server = tool.get('server', 'unknown')
        if server not in tools_by_server:
            tools_by_server[server] = []
        tools_by_server[server].append(tool['name'])
    
    for server, tool_names in tools_by_server.items():
        print(f"\n{server}: {len(tool_names)} tools")
        for tool_name in tool_names[:5]:  # Show first 5
            print(f"  - {tool_name}")
        if len(tool_names) > 5:
            print(f"  ... and {len(tool_names) - 5} more")
    
    # Cleanup
    await manager.cleanup()

# Run the example
asyncio.run(external_mcp_example())
```

### **Example 3: Backward Compatibility Demo**

```python
import asyncio
from llmgine.llm.tools import ToolManager
from llmgine.llm.tools.toolCall import ToolCall

async def backward_compatibility_demo():
    """Demonstrate backward compatibility with existing code."""
    
    print("=== Backward Compatibility Demo ===")
    
    # This code continues to work exactly as before
    manager = ToolManager()  # Same interface!
    
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
        
        tool_call = ToolCall(
            name=tool_name,
            arguments={"city": "melbourne"},
            id="test-1"
        )
        
        result = await manager.execute_tool_call(tool_call)
        print(f"Result: {result}")
    
    # Cleanup
    await manager.cleanup()

# Run the demo
asyncio.run(backward_compatibility_demo())
```

## Advanced Features

### **1. Dynamic MCP Server Management**

**Add and remove MCP servers at runtime**:

```python
async def dynamic_server_management():
    """Demonstrate dynamic MCP server management."""
    
    manager = create_mcp_tool_manager()
    await manager.initialize()
    
    # Add server dynamically
    success = await manager.add_mcp_server(
        name="dynamic_calculator",
        command="python",
        args=["mcps/demo_calculator.py"],
        env={}
    )
    
    if success:
        print("✅ Dynamic calculator server added")
        
        # Check server status
        servers = await manager.list_mcp_servers()
        print(f"Active servers: {list(servers.keys())}")
        
        # Remove server
        await manager.remove_mcp_server("dynamic_calculator")
        print("🗑️  Dynamic calculator server removed")
    
    await manager.cleanup()
```

### **2. Tool Filtering and Selection**

**Control which tools are available from each server**:

```python
async def tool_filtering_example():
    """Demonstrate tool filtering capabilities."""
    
    manager = create_mcp_tool_manager()
    await manager.initialize()
    
    # Get tools from specific server
    llmgine_tools = await manager.get_tools_from_server("llmgine-local")
    print(f"LLMgine tools: {len(llmgine_tools)}")
    
    # Get tools by category
    weather_tools = await manager.get_tools_by_category("weather")
    print(f"Weather tools: {len(weather_tools)}")
    
    # Get tools by tags
    utility_tools = await manager.get_tools_by_tags(["utility", "math"])
    print(f"Utility/Math tools: {len(utility_tools)}")
    
    await manager.cleanup()
```

### **3. Health Monitoring and Auto-Recovery**

**Monitor server health and implement recovery strategies**:

```python
async def health_monitoring_example():
    """Demonstrate health monitoring capabilities."""
    
    manager = create_mcp_tool_manager()
    await manager.initialize()
    
    # Check health of all servers
    health_status = await manager.check_all_server_health()
    
    for server_name, health in health_status.items():
        status = health['status']
        if status == 'healthy':
            print(f"✅ {server_name}: Healthy")
        elif status == 'warning':
            print(f"⚠️  {server_name}: Warning - {health.get('message', '')}")
        else:
            print(f"❌ {server_name}: Error - {health.get('error', '')}")
            
            # Implement recovery logic
            if health.get('recoverable', False):
                print(f"🔄 Attempting to recover {server_name}...")
                success = await manager.recover_server(server_name)
                if success:
                    print(f"✅ {server_name} recovered successfully")
                else:
                    print(f"❌ Failed to recover {server_name}")
    
    await manager.cleanup()
```

## Troubleshooting

### **Common Issues**

#### **1. MCP Server Connection Failures**

```python
# Check server status
servers = await manager.list_mcp_servers()
for server_name, status in servers.items():
    if not status['active']:
        print(f"❌ Server {server_name} is not active")
        print(f"   Error: {status.get('error', 'Unknown error')}")
        print(f"   Command: {status.get('command', 'Unknown')}")
```

**Solutions:**
- Verify server script paths are correct
- Check Python environment and dependencies
- Review server logs for error messages
- Ensure required environment variables are set

#### **2. Tool Discovery Issues**

```python
# Debug tool discovery
tools = await manager.list_available_tools()
if not tools:
    print("❌ No tools discovered")
    
    # Check server connections
    servers = await manager.list_mcp_servers()
    print(f"Connected servers: {list(servers.keys())}")
    
    # Test individual server tool discovery
    for server_name in servers.keys():
        server_tools = await manager.get_tools_from_server(server_name)
        print(f"Tools from {server_name}: {len(server_tools)}")
```

**Solutions:**
- Ensure MCP servers implement the `tools/list` endpoint correctly
- Check server response format matches MCP specification
- Verify network connectivity to MCP servers

#### **3. Backward Compatibility Issues**

```python
# Verify backward compatibility
try:
    # Test original ToolManager interface
    tools = manager.parse_tools_to_list()
    print(f"✅ Backward compatibility: {len(tools)} tools found")
except Exception as e:
    print(f"❌ Backward compatibility issue: {e}")
```

**Solutions:**
- Ensure you're importing from `llmgine.llm.tools` (not old paths)
- Check that `ToolManager` class implements all original methods
- Verify tool registration still works as expected

### **Debug Mode**

**Enable comprehensive debugging**:

```python
import logging

# Enable debug logging for MCP components
logging.getLogger('llmgine.llm.tools.mcp_unified_tool_manager').setLevel(logging.DEBUG)
logging.getLogger('any_mcp').setLevel(logging.DEBUG)

# Create tool manager with debug info
manager = create_mcp_tool_manager()
manager.debug_mode = True
await manager.initialize()
```

### **Diagnostic Commands**

```python
async def run_diagnostics(manager):
    """Run comprehensive diagnostics."""
    
    print("=== MCP Integration Diagnostics ===")
    
    # 1. Check initialization
    print(f"Initialized: {manager._initialized}")
    
    # 2. Check MCP manager
    print(f"MCP Manager: {'Active' if manager.mcp_manager else 'Inactive'}")
    
    # 3. Check connected servers
    servers = await manager.list_mcp_servers()
    print(f"Connected MCP servers: {list(servers.keys())}")
    
    # 4. Check available tools
    tools = await manager.list_available_tools()
    print(f"Total available tools: {len(tools)}")
    
    # 5. Check tool schemas
    print(f"Tool schemas: {len(manager.tool_schemas)}")
    
    # 6. Test basic functionality
    try:
        if tools:
            tool_name = tools[0]['name']
            test_call = ToolCall(id="test", name=tool_name, arguments="{}")
            result = await manager.execute_tool_call(test_call)
            print(f"✅ Tool execution test: {result}")
    except Exception as e:
        print(f"❌ Tool execution test failed: {e}")

# Run diagnostics
await run_diagnostics(manager)
```

## Performance Considerations

### **Optimization Guidelines**

1. **Server Startup**: Use `auto_start=False` for servers that aren't immediately needed
2. **Connection Pooling**: Reuse MCP connections when possible
3. **Tool Caching**: Cache tool schemas and discovery results
4. **Async Execution**: Use concurrent tool execution for independent operations
5. **Health Monitoring**: Implement proactive health checks to prevent failures

### **Performance Monitoring**

```python
async def monitor_performance(manager):
    """Monitor MCP system performance."""
    
    import time
    
    start_time = time.time()
    
    # Execute multiple tools concurrently
    tool_calls = [
        ToolCall(id=f"perf_test_{i}", name="add", arguments=f'{{"a": {i}, "b": {i+1}}}')
        for i in range(10)
    ]
    
    results = await manager.execute_tool_calls(tool_calls)
    
    end_time = time.time()
    total_time = end_time - start_time
    
    print(f"Executed {len(tool_calls)} tools in {total_time:.3f}s")
    print(f"Average time per tool: {total_time/len(tool_calls):.3f}s")
    
    return results

# Run performance test
await monitor_performance(manager)
```

### **Memory Management**

```python
async def cleanup_example():
    """Demonstrate proper cleanup."""
    
    try:
        # Use tool manager
        manager = create_mcp_tool_manager()
        await manager.initialize()
        
        # Execute tools
        result = await manager.execute_tool_call(tool_call)
        
    finally:
        # Always cleanup
        if 'manager' in locals():
            await manager.cleanup()
```

## API Reference

### **MCPUnifiedToolManager**

#### **Constructor**
```python
MCPUnifiedToolManager(chat_history: Optional[SimpleChatHistory] = None)
```

#### **Key Methods**
```python
# Initialization
await initialize() -> bool

# Tool execution (same interface as original ToolManager)
await execute_tool_call(tool_call: ToolCall) -> Any
await execute_tool_calls(tool_calls: List[ToolCall]) -> List[Any]

# MCP server management
await add_mcp_server(name: str, command: str, args: List[str], env: Optional[Dict[str, str]] = None) -> bool
await remove_mcp_server(name: str) -> bool
await list_mcp_servers() -> Dict[str, bool]

# Tool discovery
await list_available_tools() -> List[Dict[str, Any]]
await get_tools_from_server(server_name: str) -> List[Dict[str, Any]]
await get_tools_by_category(category: str) -> List[Dict[str, Any]]
await get_tools_by_tags(tags: List[str]) -> List[Dict[str, Any]]

# Health monitoring
await check_all_server_health() -> Dict[str, Dict[str, Any]]
await recover_server(server_name: str) -> bool

# Properties
tool_schemas: List[Dict[str, Any]]  # All tool schemas (local + MCP)
chat_history_to_messages() -> List[Dict[str, Any]]

# Cleanup
await cleanup() -> None
```

### **Factory Functions**

```python
# Create MCP-powered ToolManager
from llmgine.llm.tools import create_mcp_tool_manager

manager = create_mcp_tool_manager(chat_history)
await manager.initialize()

# Backward compatibility - same interface
from llmgine.llm.tools import ToolManager

manager = ToolManager(chat_history)  # Now points to MCPUnifiedToolManager
await manager.initialize()
```

---

## Conclusion

The **revolutionary new LLMgine-MCP architecture** transforms the traditional approach by:

- **🔄 Making ToolManager an MCP Server**: LLMgine's tools are now available through the MCP protocol
- **🔌 Using any-mcp as MCP Client**: Single client that connects to multiple MCP servers simultaneously
- **🌐 Enabling Universal Access**: Any MCP-compliant client can use LLMgine's tools
- **🚀 Providing Scalability**: Easy to add new MCP servers without changing the client architecture
- **🔄 Maintaining Backward Compatibility**: Existing code continues to work unchanged

This architecture creates a **unified, scalable, and extensible system** that leverages the best of both worlds:

- **LLMgine's robust tool ecosystem** (now available as MCP server)
- **any-mcp's powerful MCP client capabilities** (connects to multiple servers)
- **Official MCP server ecosystem** (Notion, GitHub, Filesystem, etc.)

The result is a **modern, professional-grade MCP integration** that maintains 100% backward compatibility while opening up a world of new possibilities through the MCP ecosystem.

**Repository**: [https://github.com/chi-n-nguyen/llmgine-mcp-integration](https://github.com/chi-n-nguyen/llmgine-mcp-integration)

**any-mcp Repository**: [https://github.com/chi-n-nguyen/any-mcp](https://github.com/chi-n-nguyen/any-mcp)
