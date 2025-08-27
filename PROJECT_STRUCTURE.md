# Project Structure & Architecture

![Project Structure Workflow Diagram](project_structure_workflow_diagram.png)

## 🚀 **Revolutionary New Architecture**

This project has undergone a **complete architectural transformation** that flips the traditional approach on its head:

- **🔄 ToolManager as MCP Server**: LLMgine's existing tools are now available through the MCP protocol
- **🔌 any-mcp as MCP Client**: Single client that can connect to multiple MCP servers simultaneously
- **🌐 Universal Access**: Any MCP-compliant client can now use LLMgine's tools
- **🚀 Scalability**: Easy to add new MCP servers without changing the client architecture

## 📁 **Current Directory Structure**

```
any-mcp/
├── pyproject.toml                    # Project configuration and dependencies
├── main.py                           # Entry point script
├── README.md                         # Project documentation
├── LICENSE                           # MIT License
├── VERSION                           # Version tracking
├── CLAUDE.md                         # AI assistant guide for contributors
├── PROJECT_STRUCTURE.md              # This file
├── README_MCP_INTEGRATION.md         # MCP integration documentation
├── config.py                         # Configuration utilities
├── setup_team.sh                     # Team setup script
├── uv.lock                           # Dependency lock file
│
├── config/                           # Configuration files
│   ├── mcp_config.yaml              # MCP configuration
│   └── mcp_servers_example.yaml     # Example MCP server configurations
│
├── demos/                            # Working examples and demonstrations
│   ├── integration/                  # Advanced integration patterns
│   ├── notion/                       # Notion MCP integration demos
│   └── tools/                        # MCP tool combination examples
│
├── discordmcp/                       # Discord MCP server implementation
│   ├── src/                          # TypeScript source code
│   ├── package.json                  # Node.js dependencies
│   └── README.md                     # Discord MCP server documentation
│
├── docs/                             # Documentation
│   ├── llmgine-mcp-integration.md    # LLMgine MCP integration guide
│   └── ...                           # Additional documentation
│
├── examples/                         # Example scripts and use cases
│   └── llmgine_integration_example.py # LLMgine integration example
│
├── llmgine-mcp-integration/          # 🆕 LLMgine MCP integration repository
│   └── llmgine-mcp-integration/      # Nested repository with complete integration
│       ├── src/                      # Source code
│       │   ├── any_mcp/              # Your any-mcp implementation (copied)
│       │   │   ├── core/             # Core MCP functionality
│       │   │   ├── managers/         # MCP management
│       │   │   ├── integration/      # LLMgine integration layer
│       │   │   ├── api/              # Web API components
│       │   │   ├── cli/              # CLI interface
│       │   │   └── servers/          # Server connectors
│       │   └── llmgine/              # LLMgine integration layer
│       │       └── llm/tools/        # Tool management
│       │           ├── mcp_unified_tool_manager.py    # 🆕 Unified MCP ToolManager
│       │           ├── mcp_config_loader.py           # 🆕 Configuration system
│       │           └── __init__.py                    # 🆕 Updated imports
│       ├── mcps/                     # MCP server implementations
│       │   ├── llmgine_local_tools.py # 🆕 LLMgine tools as MCP server
│       │   └── demo_calculator.py    # Calculator demo server
│       ├── config/                   # MCP server configuration
│       │   └── mcp_servers_config.yaml # 🆕 Pre-configured MCP servers
│       ├── examples/                 # Integration examples
│       │   ├── mcp_unified_demo.py   # 🆕 Comprehensive demo script
│       │   └── test_mcp_integration.py # 🆕 Integration test script
│       ├── MCP_INTEGRATION_COMPLETE.md # 🆕 Complete integration summary
│       └── showcase_demo.py          # 🆕 Architecture showcase
│
├── mcp-adapter/                      # Separate MCP adapter repository
│   ├── src/                          # Source code
│   ├── demos/                        # Adapter demos
│   ├── docs/                         # Adapter documentation
│   └── pyproject.toml                # Adapter configuration
│
├── mcps/                             # MCP server examples and implementations
│   └── demo_calculator.py            # Calculator demo server
│
├── programs/                          # Program implementations
│   └── engines/                      # Engine implementations
│       └── mcp_tool_chat_engine.py   # MCP tool chat engine
│
├── scripts/                           # Utility scripts
│   └── migrate_to_mcp.py             # Migration script
│
├── src/                              # Legacy source code (cleaned up)
│   ├── llmgine/                      # LLMgine integration layer
│   │   └── llm/tools/                # Tool management (cleaned)
│   └── universal_mcp_adapter/        # Universal MCP adapter
│
├── tests/                             # Test suite
│   ├── __init__.py
│   ├── conftest.py                   # Test configuration
│   ├── integration/                   # Integration tests
│   └── unit/                         # Unit tests
│
├── tools_for_mcp_server/              # MCP server tools and utilities
│   ├── config_mcp_tools_path.py      # Tool path configuration
│   ├── discord_mcp_server_tools/      # Discord MCP server tools
│   ├── notion_mcp_server_tools/       # Notion MCP server tools
│   └── tool_mcp_server_loading_package/ # Tool loading package
│
├── yaml_config/                       # YAML configuration examples
│   ├── example_mcp_config.yaml        # Example MCP configuration
│   └── mcp_config.yaml                # MCP configuration
│
└── .claude/                           # Claude AI assistant files
    └── README.md                      # Claude usage guide
```

## 🏗️ **New Architecture Components**

### **1. LLMgine ToolManager as MCP Server** (`llmgine-mcp-integration/mcps/llmgine_local_tools.py`)

**LLMgine's ToolManager is now an MCP server** that exposes all existing tools through the MCP protocol:

```python
class LLMgineLocalToolsServer:
    """MCP Server that exposes LLMgine's local tools."""
    
    def __init__(self):
        self.server = Server("llmgine-local-tools")
        
        # Register local tool functions
        self.local_tools = {
            "get_weather": get_weather,           # Real weather from BOM API
            "get_station_list": get_station_list, # List available weather stations
            "simple_get_weather": simple_get_weather, # Simple demo weather
        }
        
        # Set up MCP handlers
        self._setup_handlers()
```

**Key Features:**
- **MCP Protocol Compliance**: Implements full MCP server specification
- **Tool Schema Generation**: Automatically generates OpenAPI schemas from LLMgine functions
- **Async Support**: Handles both sync and async tool functions
- **Error Handling**: Robust error handling with detailed logging

### **2. any-mcp as MCP Client** (`llmgine-mcp-integration/src/any_mcp/`)

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
```

**Key Features:**
- **Unified MCP Client**: Single client that connects to multiple MCP servers
- **Automatic Server Management**: Starts and manages all configured MCP servers
- **Tool Discovery**: Automatically discovers tools from all connected servers
- **Backward Compatibility**: Maintains exact same interface as original ToolManager

### **3. Configuration System** (`llmgine-mcp-integration/config/mcp_servers_config.yaml`)

**YAML-based configuration** for all MCP servers:

```yaml
mcp_servers:
  # LLMgine ToolManager as MCP server (always enabled)
  llmgine-local:
    type: "local" 
    command: "python"
    args: ["mcps/llmgine_local_tools.py"]
    enabled: true
    description: "LLMgine's built-in tools wrapped as MCP server"
    
  # Official MCP Servers (require installation)
  notion:
    type: "npm"
    command: "npx"
    args: ["@notionhq/notion-mcp-server"]
    enabled: false
    env_vars:
      NOTION_TOKEN: "${NOTION_API_TOKEN}"
    description: "Official Notion MCP server with 18+ tools"
```

## 🔄 **Architecture Flow**

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

## 🎯 **Key Benefits of New Architecture**

1. **🔄 ToolManager as MCP Server**: LLMgine's existing tools are now available through the MCP protocol
2. **🔌 any-mcp as MCP Client**: Single client that can connect to multiple MCP servers simultaneously
3. **🌐 Universal Access**: Any MCP-compliant client can now use LLMgine's tools
4. **🚀 Scalability**: Easy to add new MCP servers without changing the client architecture
5. **🔄 Backward Compatibility**: Existing LLMgine code continues to work unchanged
6. **🔧 Unified Management**: Single interface for all tools (local + external MCP servers)

## 🚀 **Getting Started**

### **1. Start LLMgine ToolManager as MCP Server**

```bash
# Start LLMgine ToolManager as MCP server
cd llmgine-mcp-integration/llmgine-mcp-integration
python mcps/llmgine_local_tools.py

# This exposes LLMgine's tools through MCP protocol
```

### **2. Connect any-mcp as MCP Client**

```python
from llmgine.llm.tools import ToolManager, create_mcp_tool_manager

# Create unified MCP tool manager
manager = create_mcp_tool_manager()

# Initialize MCP system (connects to all configured servers)
await manager.initialize()

# Get available tools from ALL connected MCP servers
tools = await manager.list_available_tools()
print(f"Available tools: {len(tools)}")
```

### **3. Add External MCP Servers**

```python
# Add Notion MCP server
await manager.add_mcp_server(
    name="notion",
    command="npx",
    args=["@notionhq/notion-mcp-server"],
    env={"NOTION_TOKEN": "your-token"}
)

# Now you have access to:
# - LLMgine tools (via ToolManager MCP server)
# - Notion tools (via Notion MCP server)
# - All through the same unified interface!
```

## 📚 **Documentation Structure**

- **`docs/llmgine-mcp-integration.md`**: Complete LLMgine MCP integration guide
- **`llmgine-mcp-integration/MCP_INTEGRATION_COMPLETE.md`**: Implementation summary
- **`llmgine-mcp-integration/showcase_demo.py`**: Architecture showcase
- **`llmgine-mcp-integration/examples/mcp_unified_demo.py`**: Working examples

## 🧪 **Testing & Examples**

- **`llmgine-mcp-integration/test_mcp_integration.py`**: Integration tests
- **`llmgine-mcp-integration/examples/mcp_unified_demo.py`**: Comprehensive demo
- **`demos/`**: Working examples and demonstrations
- **`tests/`**: Test suite with unit and integration tests

## 🔧 **Configuration & Setup**

- **`config/mcp_servers_config.yaml`**: MCP server configuration
- **`llmgine-mcp-integration/config/mcp_servers_config.yaml`**: Pre-configured servers
- **`yaml_config/`**: YAML configuration examples
- **`setup_team.sh`**: Team setup script

## 🌟 **What Makes This Special**

1. **Revolutionary Architecture**: First time ToolManager becomes an MCP server
2. **Unified Client System**: any-mcp connects to multiple MCP servers simultaneously
3. **100% Backward Compatibility**: Existing code continues to work unchanged
4. **Professional Grade**: Production-ready MCP integration system
5. **Extensible Ecosystem**: Easy to add new MCP servers and capabilities

## 🚀 **Future Vision**

This architecture creates a **unified, scalable, and extensible system** that leverages:

- **LLMgine's robust tool ecosystem** (now available as MCP server)
- **any-mcp's powerful MCP client capabilities** (connects to multiple servers)
- **Official MCP server ecosystem** (Notion, GitHub, Filesystem, etc.)
- **Community-driven growth** (easy to add new MCP servers)

The result is a **modern, professional-grade MCP integration** that maintains 100% backward compatibility while opening up a world of new possibilities through the MCP ecosystem.

## 📖 **Repository Links**

- **Main Repository**: [https://github.com/chi-n-nguyen/any-mcp](https://github.com/chi-n-nguyen/any-mcp)
- **LLMgine Integration**: [https://github.com/chi-n-nguyen/llmgine-mcp-integration](https://github.com/chi-n-nguyen/llmgine-mcp-integration)
- **MCP Adapter**: [https://github.com/chi-n-nguyen/mcp-adapter](https://github.com/chi-n-nguyen/mcp-adapter)

---

**This is not just a project structure update - it's a complete architectural revolution that transforms how LLMgine and MCP systems work together!** 🚀