# Claude Code Quick Reference

Welcome to the **any-mcp** project! This directory contains Claude-specific guidance.

## 🚀 Quick Start

1. **Read [CLAUDE.md](../CLAUDE.md)** - Comprehensive contributor guide
2. **Check [README.md](../README.md)** - Project overview and demos
3. **Explore [demos/](../demos/)** - Working examples to understand the codebase

## 🔑 Key Files for Contributors

- **`any_mcp/core/claude.py`** - Claude integration implementation
- **`any_mcp/core/chat.py`** - Chat interface with tool calling
- **`any_mcp/managers/manager.py`** - MCP server management
- **`config.py`** - Environment configuration

## 🧪 Testing Your Changes

```bash
# Run tests
pytest

# Test Claude integration
python3 -c "from any_mcp.core.claude import Claude; print('✅ Working!')"

# Run demos
cd demos/notion && python test_real_notion.py
```

## 📚 What This Project Does

**any-mcp** eliminates the need to write custom API code by providing:
- Universal MCP server integration
- Ready-to-use tools for external services (Notion, Discord, etc.)
- Multi-LLM support (Claude, Gemini, OpenAI)
- Professional tool access without coding

## 🎯 Common Tasks

- **Add new MCP server** → Check `config/mcp_config.yaml`
- **Create new tools** → Look at `tools_for_mcp_server/`
- **Test integrations** → Use `demos/` examples
- **Debug issues** → Check `tests/` for patterns

---

**Need help? Start with [CLAUDE.md](../CLAUDE.md) for detailed guidance!**

