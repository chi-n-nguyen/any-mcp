# LLMgine-MCP Integration Guide

## Overview

This document provides a comprehensive guide to the integration between **LLMgine** and the **Model Context Protocol (MCP)** system. The integration replaces LLMgine's original ToolManager with a powerful MCP-based system that provides enhanced tool management, dynamic discovery, and seamless integration with external tool providers.

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Key Components](#key-components)
3. [Getting Started](#getting-started)
4. [Migration Guide](#migration-guide)
5. [Configuration](#configuration)
6. [Usage Examples](#usage-examples)
7. [Advanced Features](#advanced-features)
8. [Troubleshooting](#troubleshooting)
9. [Performance Considerations](#performance-considerations)
10. [API Reference](#api-reference)

## Architecture Overview

The MCP integration provides a seamless bridge between LLMgine's existing architecture and the MCP ecosystem:

```
┌─────────────────────┐    ┌──────────────────────┐    ┌─────────────────────┐
│   LLMgine Engine    │    │   MCP Integration    │    │    MCP Servers      │
│                     │    │                      │    │                     │
│ ┌─────────────────┐ │    │ ┌──────────────────┐ │    │ ┌─────────────────┐ │
│ │ ToolChatEngine  │◄┼────┼►│ MCPToolManager   │◄┼────┼►│ Calculator      │ │
│ └─────────────────┘ │    │ └──────────────────┘ │    │ └─────────────────┘ │
│                     │    │                      │    │                     │
│ ┌─────────────────┐ │    │ ┌──────────────────┐ │    │ ┌─────────────────┐ │
│ │ MessageBus      │◄┼────┼►│ LLMgineMCPBridge │◄┼────┼►│ Notion          │ │
│ └─────────────────┘ │    │ └──────────────────┘ │    │ └─────────────────┘ │
│                     │    │                      │    │                     │
│ ┌─────────────────┐ │    │ ┌──────────────────┐ │    │ ┌─────────────────┐ │
│ │ Event System    │◄┼────┼►│ Event Handlers   │◄┼────┼►│ Custom Tools    │ │
│ └─────────────────┘ │    │ └──────────────────┘ │    │ └─────────────────┘ │
└─────────────────────┘    └──────────────────────┘    └─────────────────────┘
```

### Key Benefits

- **Drop-in Replacement**: MCPToolManager implements the same interface as the original ToolManager
- **Enhanced Capabilities**: Dynamic tool discovery, server health monitoring, and advanced lifecycle management
- **Event-Driven**: Full integration with LLMgine's MessageBus system
- **Backwards Compatible**: Existing local tools continue to work seamlessly
- **Extensible**: Easy to add new MCP servers and tool providers

## Key Components

### 1. MCPToolManager (`src/llmgine/llm/tools/mcp_tool_manager.py`)

The core replacement for LLMgine's original ToolManager:

```python
from llmgine.llm.tools.mcp_tool_manager import MCPToolManager, MCPServerConfig

# Create MCP tool manager
tool_manager = MCPToolManager(chat_history, session_id)

# Register local tools (backwards compatibility)
tool_manager.register_tool(my_function)

# Register MCP servers
await tool_manager.register_mcp_server(MCPServerConfig(
    name="calculator",
    command="python",
    args=["mcps/demo_calculator.py"],
    env={},
    auto_start=True
))

# Execute tools (same interface as original)
result = await tool_manager.execute_tool_call(tool_call)
```

**Key Features:**
- Same interface as original ToolManager
- Mixed execution environment (local + MCP tools)
- Automatic tool schema generation
- Health monitoring and error recovery
- Comprehensive logging and metrics

### 2. LLMgineMCPBridge (`src/llmgine/llm/tools/mcp_bridge_integration.py`)

Provides deep integration with LLMgine's MessageBus system:

```python
from llmgine.llm.tools.mcp_bridge_integration import LLMgineMCPBridge

# Create bridge integration
bridge = LLMgineMCPBridge(llmgine_bus, session_id)
await bridge.initialize()

# Register MCP server
await bridge.register_mcp_server("calculator", "python", ["calc.py"])

# Execute tools through MessageBus
result = await bridge.execute_mcp_tool("calculator", "add", {"a": 5, "b": 3})
```

**Key Features:**
- Event translation between MCP and LLMgine formats
- Command routing and execution
- Lifecycle management for MCP servers
- Rich monitoring and metrics collection

### 3. MCPServerRegistry (`src/llmgine/llm/tools/mcp_registry.py`)

Advanced server definition and discovery system:

```python
from llmgine.llm.tools.mcp_registry import MCPServerRegistry, MCPServerDefinition

# Create registry
registry = MCPServerRegistry()

# Register server definition
definition = MCPServerDefinition(
    name="notion",
    command="python",
    args=["notion_server.py"],
    description="Notion integration server",
    tags=["productivity", "documents"],
    priority=10
)

registry.register_server(definition)

# Load from configuration file
registry.load_from_file("mcp_servers.yaml")

# Discover tools
tools = await registry.discover_tools()
```

**Key Features:**
- Configuration file support (YAML/JSON)
- Server health monitoring
- Tool discovery and metadata management
- Advanced filtering and search capabilities

### 4. Enhanced ToolChatEngine (`programs/engines/mcp_tool_chat_engine.py`)

Updated engine that demonstrates the MCP integration:

```python
from programs.engines.mcp_tool_chat_engine import MCPToolChatEngine

# Create engine with MCP support
engine = MCPToolChatEngine(
    model="gpt-4o-mini",
    enable_mcp_servers=True
)

# Initialize (automatically registers default MCP servers)
await engine.initialize()

# Use normally - MCP tools are automatically available
result = await engine.handle_command(MCPToolChatEngineCommand(
    prompt="Calculate 15 * 23 and then search for information about the result"
))
```

## Getting Started

### 1. Basic Setup

Replace your existing ToolManager with MCPToolManager:

```python
# Before (original ToolManager)
from llmgine.llm.tools.tool_manager import ToolManager

tool_manager = ToolManager(chat_history)
tool_manager.register_tool(my_function)

# After (MCP ToolManager)
from llmgine.llm.tools.mcp_tool_manager import MCPToolManager

tool_manager = MCPToolManager(chat_history, session_id)
await tool_manager.initialize()  # Required for MCP functionality
tool_manager.register_tool(my_function)  # Still works!
```

### 2. Add MCP Servers

```python
from llmgine.llm.tools.mcp_tool_manager import MCPServerConfig

# Define MCP servers
servers = [
    MCPServerConfig(
        name="calculator",
        command="python",
        args=["mcps/demo_calculator.py"],
        env={},
        auto_start=True
    ),
    MCPServerConfig(
        name="notion",
        command="python",
        args=["all_mcp_servers/notion_mcp_server.py"],
        env={"NOTION_TOKEN": "your_token_here"},
        auto_start=True
    )
]

# Register servers
results = await tool_manager.register_mcp_servers(servers)
print(f"Registered {sum(results.values())}/{len(servers)} servers successfully")
```

### 3. Use Enhanced Engine

```python
from programs.engines.mcp_tool_chat_engine import MCPToolChatEngine

# Create and initialize engine
engine = MCPToolChatEngine(enable_mcp_servers=True)
await engine.initialize()

# Get available tools
tools_info = await engine.get_available_tools()
print(f"Available tools: {tools_info}")

# Execute commands (tools are automatically discovered and used)
result = await engine.handle_command(MCPToolChatEngineCommand(
    prompt="What's the weather in New York and create a Notion page about it?"
))
```

## Migration Guide

### From Original ToolManager

The MCPToolManager is designed as a drop-in replacement:

```python
# Migration helper
from llmgine.llm.tools.mcp_tool_manager import ToolManagerMigrationHelper

# Automatic migration
mcp_manager = ToolManagerMigrationHelper.migrate_from_original(
    original_tool_manager,
    session_id="my_session"
)

# Hybrid approach (original tools + MCP servers)
hybrid_manager = ToolManagerMigrationHelper.create_hybrid_manager(
    original_tool_manager,
    mcp_server_configs,
    session_id="my_session"
)
```

### Update Engine Code

Minimal changes required for existing engines:

```python
# Before
from llmgine.llm.tools.tool_manager import ToolManager

class MyEngine:
    def __init__(self):
        self.tool_manager = ToolManager(self.chat_history)
        self.tool_manager.register_tool(my_function)

# After
from llmgine.llm.tools.mcp_tool_manager import MCPToolManager

class MyEngine:
    def __init__(self):
        self.tool_manager = MCPToolManager(self.chat_history, str(self.session_id))
        self._initialized = False
    
    async def initialize(self):
        if not self._initialized:
            await self.tool_manager.initialize()
            self.tool_manager.register_tool(my_function)
            # Optionally add MCP servers
            await self._register_mcp_servers()
            self._initialized = True
```

## Configuration

### Configuration Files

Create `mcp_servers.yaml` for server definitions:

```yaml
mcp_servers:
  - name: calculator
    command: python
    args: ["mcps/demo_calculator.py"]
    description: "Basic calculator operations"
    tags: ["math", "utility"]
    auto_start: true
    priority: 50
    
  - name: notion
    command: python
    args: ["all_mcp_servers/notion_mcp_server.py"]
    env:
      NOTION_TOKEN: "${NOTION_TOKEN}"
    description: "Notion workspace integration"
    tags: ["productivity", "documents"]
    auto_start: true
    priority: 10
    python_requirements:
      - "notion-client>=2.0.0"
    
  - name: web_search
    command: python
    args: ["servers/web_search.py"]
    description: "Web search capabilities"
    tags: ["search", "web"]
    auto_start: false  # Manual start
    priority: 30
    include_tools: ["search", "summarize"]  # Only these tools
    exclude_tools: ["admin_search"]  # Exclude this tool
```

### Environment Variables

```bash
# MCP system configuration
export MCP_LOG_LEVEL=INFO
export MCP_EXECUTION_TIMEOUT=30
export MCP_MAX_RETRIES=3

# Server-specific configuration
export NOTION_TOKEN=your_notion_token
export OPENAI_API_KEY=your_openai_key
```

### Registry Configuration

```python
from llmgine.llm.tools.mcp_registry import MCPServerRegistry

# Create registry with custom config directory
registry = MCPServerRegistry(config_dir="./my_mcp_config")

# Load all configurations from directory
loaded_count = registry.load_from_directory()

# Get registry statistics
stats = registry.get_registry_stats()
print(f"Loaded {stats['total_servers']} servers with {stats['total_tools']} tools")
```

## Usage Examples

### Example 1: Basic Tool Execution

```python
import asyncio
from llmgine.llm.tools.mcp_tool_manager import MCPToolManager, MCPServerConfig
from llmgine.llm.context.memory import SimpleChatHistory
from llmgine.llm.tools.toolCall import ToolCall

async def basic_example():
    # Setup
    chat_history = SimpleChatHistory()
    tool_manager = MCPToolManager(chat_history, "example_session")
    
    # Initialize
    await tool_manager.initialize()
    
    # Register MCP server
    calculator_config = MCPServerConfig(
        name="calculator",
        command="python",
        args=["mcps/demo_calculator.py"],
        env={},
        auto_start=True
    )
    
    success = await tool_manager.register_mcp_server(calculator_config)
    if success:
        print("Calculator server registered successfully")
    
    # Execute tool
    tool_call = ToolCall(
        id="calc_001",
        name="add",
        arguments='{"a": 15, "b": 27}'
    )
    
    result = await tool_manager.execute_tool_call(tool_call)
    print(f"15 + 27 = {result}")
    
    # Cleanup
    await tool_manager.cleanup()

asyncio.run(basic_example())
```

### Example 2: MessageBus Integration

```python
import asyncio
from llmgine.bus.bus import MessageBus
from llmgine.llm.tools.mcp_bridge_integration import create_llmgine_mcp_integration

async def messagebus_example():
    # Create and start MessageBus
    bus = MessageBus()
    await bus.start()
    
    # Create MCP integration
    mcp_servers = [
        {
            "name": "calculator",
            "command": "python",
            "args": ["mcps/demo_calculator.py"],
            "env": {}
        }
    ]
    
    bridge = await create_llmgine_mcp_integration(
        bus,
        "messagebus_session",
        mcp_servers
    )
    
    # Execute tool through MessageBus
    result = await bridge.execute_mcp_tool(
        "calculator",
        "multiply",
        {"a": 6, "b": 7}
    )
    
    print(f"6 * 7 = {result['result']}")
    
    # Get metrics
    metrics = await bridge.get_mcp_metrics()
    print(f"Execution metrics: {metrics}")
    
    # Cleanup
    await bridge.cleanup()
    await bus.stop()

asyncio.run(messagebus_example())
```

### Example 3: Complete Engine Integration

```python
import asyncio
from programs.engines.mcp_tool_chat_engine import MCPToolChatEngine, MCPToolChatEngineCommand
from llmgine.llm.tools.mcp_tool_manager import MCPServerConfig

async def engine_example():
    # Create custom MCP server configurations
    custom_servers = [
        MCPServerConfig(
            name="weather",
            command="python",
            args=["servers/weather_server.py"],
            env={"API_KEY": "your_weather_api_key"},
            auto_start=True
        ),
        MCPServerConfig(
            name="calculator",
            command="python", 
            args=["mcps/demo_calculator.py"],
            env={},
            auto_start=True
        )
    ]
    
    # Create engine with custom servers
    engine = MCPToolChatEngine(
        model="gpt-4o-mini",
        enable_mcp_servers=True,
        mcp_server_configs=custom_servers
    )
    
    # Initialize
    await engine.initialize()
    
    # Check available tools
    tools_info = await engine.get_available_tools()
    print(f"Local tools: {tools_info['local_tools']}")
    print(f"MCP tools: {len(tools_info['mcp_tools'])}")
    
    # Execute command
    command = MCPToolChatEngineCommand(
        prompt="What's 25 * 34, and if that's the temperature in Celsius, what is it in Fahrenheit?"
    )
    
    result = await engine.handle_command(command)
    print(f"Result: {result.result}")
    
    # Get execution metrics
    metrics = await engine.get_metrics()
    print(f"Performance metrics: {metrics}")
    
    # Cleanup
    await engine.cleanup()

asyncio.run(engine_example())
```

## Advanced Features

### 1. Event Monitoring

Monitor tool execution lifecycle:

```python
from llmgine.llm.tools.mcp_bridge_integration import MCPToolExecutionLLMgineEvent

async def tool_execution_handler(event: MCPToolExecutionLLMgineEvent):
    if event.success:
        print(f"✅ Tool {event.tool_name} completed in {event.execution_time_ms}ms")
    else:
        print(f"❌ Tool {event.tool_name} failed: {event.error_message}")

# Register event handler
bus.register_event_handler(
    MCPToolExecutionLLMgineEvent,
    tool_execution_handler,
    session_id
)
```

### 2. Dynamic Server Management

Add and remove servers at runtime:

```python
# Add server dynamically
new_server_config = MCPServerConfig(
    name="dynamic_server",
    command="python",
    args=["new_server.py"],
    env={},
    auto_start=True
)

success = await tool_manager.register_mcp_server(new_server_config)
if success:
    print("Dynamic server added successfully")

# Check server status
status = await tool_manager.get_mcp_server_status()
for server_name, server_status in status.items():
    print(f"{server_name}: {'Active' if server_status['active'] else 'Inactive'}")
```

### 3. Tool Filtering and Selection

Control which tools are available:

```python
# Server definition with tool filtering
filtered_server = MCPServerDefinition(
    name="filtered_server",
    command="python",
    args=["multi_tool_server.py"],
    include_tools=["safe_tool1", "safe_tool2"],  # Only these tools
    exclude_tools=["admin_tool", "dangerous_tool"],  # Exclude these
    description="Server with filtered tools"
)

registry.register_server(filtered_server)
```

### 4. Health Monitoring

Monitor server health and auto-recovery:

```python
# Check health of all servers
health_status = await registry.health_check_all()

for server_name, health in health_status.items():
    if health["status"] == "error":
        print(f"⚠️  Server {server_name} is unhealthy: {health['error']}")
        # Implement recovery logic here
```

### 5. Performance Optimization

Configure performance settings:

```python
# Configure tool manager for high performance
tool_manager = MCPToolManager(chat_history, session_id)
await tool_manager.initialize()

# Set execution timeouts
tool_manager.execution_timeout = 10  # 10 second timeout

# Configure retry behavior
tool_manager.max_retries = 2
tool_manager.retry_delay = 1.0  # 1 second between retries

# Enable performance monitoring
tool_manager.enable_performance_monitoring = True
```

## Troubleshooting

### Common Issues

#### 1. MCP Server Connection Failures

```python
# Check server status
status = await tool_manager.get_mcp_server_status()
for server_name, info in status.items():
    if not info["active"]:
        print(f"Server {server_name} is not active")
        # Check configuration
        config = info["config"]
        print(f"Command: {config.command} {' '.join(config.args)}")
```

**Solutions:**
- Verify server script paths are correct
- Check Python environment and dependencies
- Review server logs for error messages
- Ensure required environment variables are set

#### 2. Tool Discovery Issues

```python
# Debug tool discovery
mcp_tools = await tool_manager.discover_mcp_tools()
if not mcp_tools:
    print("No MCP tools discovered")
    # Check server connection
    # Verify server implements MCP protocol correctly
```

**Solutions:**
- Ensure MCP servers implement the `tools/list` endpoint
- Check server response format matches MCP specification
- Verify network connectivity to MCP servers

#### 3. Event System Integration

```python
# Debug event flow
import logging
logging.getLogger('llmgine.llm.tools.mcp_bridge_integration').setLevel(logging.DEBUG)

# Check event handler registration
handlers = bus._registry.get_event_handlers(MCPToolExecutionLLMgineEvent, session_id)
print(f"Registered handlers: {len(handlers)}")
```

**Solutions:**
- Verify event handlers are registered with correct session ID
- Check event type matching
- Ensure MessageBus is properly initialized

### Debug Mode

Enable comprehensive debugging:

```python
import logging

# Enable debug logging for MCP components
logging.getLogger('llmgine.llm.tools.mcp_tool_manager').setLevel(logging.DEBUG)
logging.getLogger('llmgine.llm.tools.mcp_bridge_integration').setLevel(logging.DEBUG)
logging.getLogger('any_mcp').setLevel(logging.DEBUG)

# Create tool manager with debug info
tool_manager = MCPToolManager(chat_history, session_id)
tool_manager.debug_mode = True
await tool_manager.initialize()
```

### Diagnostic Commands

```python
# Get comprehensive diagnostic information
async def run_diagnostics(tool_manager):
    print("=== MCP Integration Diagnostics ===")
    
    # 1. Check initialization
    print(f"Initialized: {tool_manager._initialized}")
    
    # 2. Check local tools
    print(f"Local tools: {list(tool_manager.local_tools.keys())}")
    
    # 3. Check MCP servers
    server_status = await tool_manager.get_mcp_server_status()
    print(f"MCP servers: {server_status}")
    
    # 4. Check discovered tools
    mcp_tools = await tool_manager.discover_mcp_tools()
    print(f"MCP tools: {len(mcp_tools)}")
    
    # 5. Check tool schemas
    print(f"Total tool schemas: {len(tool_manager.tool_schemas)}")
    
    # 6. Test basic functionality
    try:
        # Test local tool if available
        if tool_manager.local_tools:
            tool_name = list(tool_manager.local_tools.keys())[0]
            test_call = ToolCall(id="test", name=tool_name, arguments="{}")
            result = await tool_manager.execute_tool_call(test_call)
            print(f"Local tool test: {result}")
    except Exception as e:
        print(f"Local tool test failed: {e}")

await run_diagnostics(tool_manager)
```

## Performance Considerations

### Optimization Guidelines

1. **Server Startup**: Use `auto_start=False` for servers that aren't immediately needed
2. **Tool Filtering**: Use `include_tools`/`exclude_tools` to limit available tools
3. **Connection Pooling**: Reuse MCP connections when possible
4. **Caching**: Cache tool schemas and discovery results
5. **Async Execution**: Use concurrent tool execution for independent operations

### Performance Monitoring

```python
# Monitor execution performance
async def monitor_performance(tool_manager):
    import time
    
    start_time = time.time()
    
    # Execute multiple tools
    tool_calls = [
        ToolCall(id=f"perf_test_{i}", name="add", arguments=f'{{"a": {i}, "b": {i+1}}}')
        for i in range(10)
    ]
    
    results = await tool_manager.execute_tool_calls(tool_calls)
    
    end_time = time.time()
    total_time = end_time - start_time
    
    print(f"Executed {len(tool_calls)} tools in {total_time:.3f}s")
    print(f"Average time per tool: {total_time/len(tool_calls):.3f}s")
    
    return results

# Run performance test
await monitor_performance(tool_manager)
```

### Memory Management

```python
# Cleanup resources properly
async def cleanup_example():
    try:
        # Use tool manager
        await tool_manager.execute_tool_calls(tool_calls)
    finally:
        # Always cleanup
        await tool_manager.cleanup()
        if bridge:
            await bridge.cleanup()
        await bus.stop()
```

## API Reference

### MCPToolManager

#### Constructor
```python
MCPToolManager(chat_history: Optional[SimpleChatHistory] = None, session_id: Optional[str] = None)
```

#### Key Methods
```python
# Initialization
await initialize() -> None

# Tool registration (backwards compatibility)
register_tool(func: AsyncOrSyncToolFunction) -> None

# MCP server management
await register_mcp_server(config: MCPServerConfig) -> bool
await register_mcp_servers(configs: List[MCPServerConfig]) -> Dict[str, bool]

# Tool execution (same interface as original)
await execute_tool_call(tool_call: ToolCall) -> Any
await execute_tool_calls(tool_calls: List[ToolCall]) -> List[Any]

# Discovery and status
await discover_mcp_tools() -> List[Dict[str, Any]]
await get_mcp_server_status() -> Dict[str, Any]

# Properties
tool_schemas: List[Dict[str, Any]]  # All tool schemas (local + MCP)
chat_history_to_messages() -> List[Dict[str, Any]]

# Cleanup
await cleanup() -> None
```

### LLMgineMCPBridge

#### Constructor
```python
LLMgineMCPBridge(llmgine_bus: MessageBus, session_id: Optional[Union[str, SessionID]] = None)
```

#### Key Methods
```python
# Initialization
await initialize() -> bool

# High-level interface
await register_mcp_server(name: str, command: str, args: list, env: Dict[str, str] = None) -> bool
await execute_mcp_tool(mcp_name: str, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]

# Information and monitoring
await get_available_tools() -> List[Dict[str, Any]]
await get_mcp_metrics() -> Dict[str, Any]
await get_server_status() -> Dict[str, Any]

# Cleanup
await cleanup() -> None
```

### MCPServerRegistry

#### Constructor
```python
MCPServerRegistry(config_dir: Optional[Union[str, Path]] = None)
```

#### Key Methods
```python
# Server definition management
register_server(definition: MCPServerDefinition) -> bool
unregister_server(name: str) -> bool
get_server_definition(name: str) -> Optional[MCPServerDefinition]
list_servers(tags: Optional[List[str]] = None, status: Optional[str] = None) -> List[MCPServerDefinition]

# Configuration file management
load_from_file(file_path: Union[str, Path]) -> int
load_from_directory(directory: Optional[Union[str, Path]] = None) -> int
save_to_file(file_path: Union[str, Path], servers: Optional[List[str]] = None) -> None

# Tool discovery
await discover_tools(server_names: Optional[List[str]] = None) -> Dict[str, List[MCPToolInfo]]
get_tool_info(tool_name: str, server_name: Optional[str] = None) -> Optional[MCPToolInfo]
list_tools(server_name: Optional[str] = None, category: Optional[str] = None, tags: Optional[List[str]] = None) -> List[MCPToolInfo]

# Health monitoring
await check_server_health(server_name: str) -> Dict[str, Any]
await health_check_all() -> Dict[str, Dict[str, Any]]

# Utilities
get_registry_stats() -> Dict[str, Any]
export_tool_schemas(output_format: str = "openai") -> List[Dict[str, Any]]
```

### Events and Commands

#### Events
```python
# LLMgine events for MCP integration
MCPToolRegisteredLLMgineEvent(mcp_name: str, tool_name: str, tool_schema: Dict[str, Any], ...)
MCPToolExecutionLLMgineEvent(mcp_name: str, tool_name: str, success: bool, result: Any, ...)
```

#### Commands
```python
# LLMgine commands for MCP integration
ExecuteMCPToolLLMgineCommand(mcp_name: str, tool_name: str, tool_arguments: Dict[str, Any], ...)
RegisterMCPServerCommand(mcp_name: str, command: str, args: list, env: Dict[str, str], ...)
```

---

## Conclusion

The LLMgine-MCP integration provides a powerful, flexible, and backwards-compatible way to enhance your LLM applications with external tool capabilities. The system is designed to be:

- **Easy to adopt**: Drop-in replacement for existing ToolManager
- **Powerful**: Advanced features like dynamic discovery and health monitoring  
- **Flexible**: Support for both local functions and external MCP servers
- **Production-ready**: Comprehensive error handling, logging, and monitoring

For additional support, examples, and advanced use cases, refer to the source code and test files in the repository.

**Repository**: [https://github.com/chi-n-nguyen/llmgine-mcp-integration](https://github.com/chi-n-nguyen/llmgine-mcp-integration)
