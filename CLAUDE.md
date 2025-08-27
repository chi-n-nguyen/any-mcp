# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**any-mcp** is a comprehensive framework for integrating MCP (Model Context Protocol) servers with Python applications. It provides a universal adapter that safely starts any MCP package and provides unified tool access, eliminating the need to write custom API code for external services.

## Key Features

- **Universal MCP Integration** - Connect to any MCP server with one line
- **18+ Notion Tools** - Create, read, update, delete pages, databases, blocks
- **Multi-LLM Support** - Claude, Gemini, and OpenAI integration
- **Extensible Framework** - Add new MCP servers without coding
- **Professional Tool Access** - Ready-to-use tools for external services

## Development Commands

### Package Management
This project uses `uv` as the package manager:
```bash
uv pip install -e .              # Install in development mode
uv pip install -e ".[dev]"       # Install with development dependencies
uv sync                          # Install from uv.lock (recommended)
```

### Environment Setup
```bash
# Activate virtual environment
source .venv/bin/activate

# Set your API tokens (never hardcode!)
export ANTHROPIC_API_KEY="your_claude_key_here"
export GEMINI_API_KEY="your_gemini_key_here"
export NOTION_TOKEN="your_notion_token_here"
```

### Testing
```bash
# Run all tests
pytest

# Run specific test categories
pytest tests/integration/
pytest tests/unit/

# Run with verbose output
pytest -sv --log-cli-level=0
```

### Code Quality
```bash
# Lint source code
ruff check src/
ruff check tests/

# Format code
ruff format src/
ruff format tests/

# Auto-fix lint issues
ruff check --fix src/

# Type checking
mypy src/
```

## Project Structure

```
mcp/
├── any_mcp/                    # Core MCP integration code
│   ├── core/                  # LLM providers (Claude, Gemini)
│   ├── api/                   # Web API endpoints
│   ├── cli/                   # Command-line interface
│   ├── managers/              # MCP server management
│   └── servers/               # Server connection handling
├── demos/                     # Working examples
│   ├── notion/               # Notion MCP integration demos
│   ├── tools/                # MCP tool combination examples
│   └── integration/          # Advanced integration patterns
├── src/                       # Additional source code
├── mcps/                      # MCP server examples
├── config/                    # Configuration files
└── tests/                     # Test suite
```

## Core Components

### **MCP Client** (`any_mcp/core/client.py`)
- Connect to any MCP server
- Handle authentication and communication
- Tool discovery and execution

### **LLM Integration** (`any_mcp/core/`)
- **Claude** (`claude.py`) - Anthropic Claude integration
- **Gemini** (`gemini.py`) - Google Gemini integration
- **Chat** (`chat.py`) - Unified chat interface

### **MCP Manager** (`any_mcp/managers/manager.py`)
- Start and manage MCP servers
- Handle server lifecycle
- Tool routing and execution

### **CLI Interface** (`any_mcp/cli/`)
- Interactive command-line tools
- Server management commands
- Natural language tool calling

## Quick Start Examples

### 1. Test Claude Integration
```bash
# Set your API key
export ANTHROPIC_API_KEY="your_key_here"

# Test Claude
python3 -c "
from any_mcp.core.claude import Claude
claude = Claude('claude-3-5-sonnet-20241022')
print('✅ Claude integration working!')
"
```

### 2. Run Notion Demo
```bash
cd demos/notion
export NOTION_TOKEN="your_token_here"
python test_real_notion.py
```

### 3. Start Interactive CLI
```bash
source .venv/bin/activate
python3 -m any_mcp.cli.main chat
```

## MCP Server Integration

### Adding New MCP Servers
1. **Create server configuration** in `config/mcp_config.yaml`
2. **Add server tools** to `tools_for_mcp_server/`
3. **Test integration** with demo scripts
4. **Update documentation** with new capabilities

### Available MCP Servers
- **Notion** - Document and database management
- **Calculator** - Math operations and functions
- **Custom** - Any MCP-compliant server

## LLM Provider Configuration

### Claude (Anthropic)
```bash
export ANTHROPIC_API_KEY="your_key_here"
export CLAUDE_MODEL="claude-3-5-sonnet-20241022"
export LLM_PROVIDER="claude"
```

### Gemini (Google)
```bash
export GEMINI_API_KEY="your_key_here"
export GEMINI_MODEL="gemini-1.5-pro"
export LLM_PROVIDER="gemini"
```

## Development Notes

- **Python 3.11+** required
- **Async-first** architecture
- **Environment variables** for all API keys (never hardcode)
- **Type hints** throughout codebase
- **Rich CLI** for user experience
- **Comprehensive testing** with pytest

## Testing Strategy

### Unit Tests
- Core functionality testing
- Mock external dependencies
- Fast execution

### Integration Tests
- MCP server communication
- LLM provider integration
- End-to-end workflows

### Demo Scripts
- Real-world usage examples
- API key required
- Manual verification

## Contributing

1. **Fork** the repository
2. **Create** a feature branch
3. **Add** your MCP server integration
4. **Test** with the demo framework
5. **Submit** a pull request

## Key Benefits for Contributors

- **No Custom API Code** - Use existing MCP servers
- **Secure** - Environment variables, no hardcoded secrets
- **Fast** - Professional tools ready to use
- **Extensible** - Add new services without coding
- **Tested** - Comprehensive test suite

---

**Ready to eliminate custom API code? Start with `demos/notion/test_real_notion.py`!**

