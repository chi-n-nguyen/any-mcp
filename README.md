# any-mcp

A comprehensive framework for integrating MCP (Model Context Protocol) servers with Python applications.

## What This Gives You

**Instead of writing custom API code for every external service, you get professional tools automatically:**

- **18+ Notion tools** - Create, read, update, delete pages, databases, blocks
- **Calculator tools** - Math operations, scientific functions
- **Discord integration** - Message handling, bot management
- **Extensible framework** - Add any MCP server with one line

## Project Structure

```
mcp/
├── demos/                    # Working examples
│   ├── notion/             # Notion MCP integration demos
│   ├── tools/              # MCP tool combination examples
│   └── integration/        # Advanced integration patterns
├── src/                     # Core MCP integration code
│   ├── any_mcp/            # MCP client and adapter implementations
│   └── llmgine/            # LLMgine integration layer
├── mcps/                    # MCP server examples
├── config/                  # Configuration files
├── docs/                    # Documentation
└── tests/                   # Test suite
```

## Quick Start

### 1. Clone and Setup
```bash
git clone <your-repo>
cd mcp
source .venv/bin/activate
```

### 2. Test Real Notion Integration
```bash
cd demos/notion
export NOTION_TOKEN="your_token_here"
python test_real_notion.py
```

### 3. Run Tool Demos
```bash
cd demos/tools
python hybrid_tool_demo.py
```

## Environment Setup

```bash
# Set your API tokens (never hardcode!)
export NOTION_TOKEN="secret_your_token_here"
export GEMINI_API_KEY="your_gemini_key_here"

# Install dependencies
uv pip install -e ".[dev]"
```

## Available Demos

### **Notion Integration** (`demos/notion/`)
- **`test_real_notion.py`** - Test with your actual Notion workspace
- **`notion_mcp_demo.py`** - See 18+ tools automatically available
- **`real_notion_mcp_demo.py`** - Full integration example

### **Tool Examples** (`demos/tools/`)
- **`hybrid_tool_demo.py`** - Combine MCP + local tools
- **`simple_interactive_demo.py`** - Interactive testing

## Core Components

### **MCP Client** (`src/any_mcp/`)
- Connect to any MCP server
- Handle authentication and communication
- Tool discovery and execution

### **MCP Adapter** (`src/llmgine/llm/tools/`)
- Integrate MCP tools with LLMgine
- Tool management and routing
- Response handling

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

## License

MIT License - see [LICENSE](LICENSE) for details.

---

**Ready to eliminate custom API code? Start with `demos/notion/test_real_notion.py`!**
