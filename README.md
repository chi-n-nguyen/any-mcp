# LLMgine with Unified MCP Integration

LLMgine enhanced with a unified MCP (Model Context Protocol) system that provides seamless access to both local tools and third-party MCP servers.

## What This Gives You

**A unified tool management system that provides:**

- **Unified Interface** - Single ToolManager for local and MCP tools
- **18+ Notion tools** - Official Notion MCP server integration
- **Local Tool Support** - Existing LLMgine tools as MCP server
- **Popular MCP Servers** - GitHub, Filesystem, SQLite, Web Search, Memory, Kubernetes, Slack
- **Configuration-Driven** - YAML-based MCP server management

## Project Structure

```
llmgine-mcp-integration/
├── src/                     # Core implementation
│   ├── any_mcp/            # Complete MCP client system
│   └── llmgine/            # LLMgine with unified MCP ToolManager
├── config/                  # MCP server configurations
│   └── mcp_servers_config.yaml
├── mcps/                    # MCP server implementations
│   ├── llmgine_local_tools.py  # Local tools as MCP server
│   └── demo_calculator.py      # Example MCP server
├── examples/                # Integration examples
│   └── mcp_unified_demo.py     # Complete usage demo
├── programs/engines/        # Enhanced engines with MCP support
├── docs/                    # Documentation
└── tests/                   # Test suite
```

## Quick Start

### 1. Clone and Setup
```bash
git clone https://github.com/chi-n-nguyen/llmgine-mcp-integration.git
cd llmgine-mcp-integration
python -m venv .venv && source .venv/bin/activate
pip install -e .
```

### 2. Configure MCP Servers
```bash
export NOTION_TOKEN="your_token_here"  # For Notion integration
export GITHUB_TOKEN="your_token_here"  # For GitHub integration
```

### 3. Run Unified Demo
```bash
python examples/mcp_unified_demo.py
```

## Environment Setup

```bash
# Set your API tokens (never hardcode!)
export NOTION_TOKEN="secret_your_token_here"
export GEMINI_API_KEY="your_gemini_key_here"

# Install dependencies
uv pip install -e ".[dev]"
```

## Key Features

### **100% Backward Compatible**
- Drop-in replacement for existing ToolManager
- No code changes required for existing applications
- Same API, enhanced with MCP capabilities

### **Unified Tool Management**
- Single interface for local and third-party tools
- Configuration-driven MCP server management
- Automatic tool discovery and registration

## Core Components

### **Unified MCP ToolManager** (`src/llmgine/llm/tools/mcp_unified_tool_manager.py`)
- Drop-in replacement for original ToolManager
- Maintains exact same interface for 100% backward compatibility
- Powered by any-mcp system
- Supports both local and third-party MCP servers

### **Configuration System** (`src/llmgine/llm/tools/mcp_config_loader.py`)
- YAML-based configuration for all MCP servers
- Environment variable support with `${VAR_NAME}` syntax
- Automatic server discovery and startup

### **Local Tools MCP Server** (`mcps/llmgine_local_tools.py`)
- Existing LLMgine tools wrapped as MCP server
- Seamless integration with unified system

## Usage Example

```python
from llmgine.llm.tools import ToolManager

# Initialize unified MCP-powered ToolManager
manager = ToolManager()
await manager.initialize()

# Works exactly like before - 100% backward compatible
tools = await manager.get_available_tools()
result = await manager.execute_tool("get_weather", {"city": "New York"})
```

## Documentation

- **[MCP Integration Guide](docs/llmgine-mcp-integration.md)** - Comprehensive guide
- **[API Reference](docs/api.md)** - Tool and client documentation
- **[Examples](demos/)** - Working code examples
- **[CLAUDE.md](CLAUDE.md)** - AI assistant guide for contributors

## Testing

```bash
# Run all tests
pytest

# Run specific test categories
pytest tests/integration/
pytest tests/unit/
```

## Key Benefits

- **No Custom API Code** - Use existing MCP servers
- **Secure** - Environment variables, no hardcoded secrets
- **Fast** - Professional tools ready to use
- **Extensible** - Add new services without coding
- **Tested** - Comprehensive test suite

## Contributing

1. **Fork** the repository
2. **Create** a feature branch
3. **Add** your MCP server integration
4. **Test** with the demo framework
5. **Submit** a pull request

### For Claude Code Contributors
- **[CLAUDE.md](CLAUDE.md)** - Comprehensive guide for Claude Code contributors
- **Development setup** - Environment configuration and testing
- **Architecture overview** - Core components and integration patterns

---

**Unified MCP integration for LLMgine - one interface for all tools!**
