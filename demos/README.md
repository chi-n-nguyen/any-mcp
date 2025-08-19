# 🚀 MCP Integration Demos

This directory contains working examples of MCP (Model Context Protocol) integration.

## 📁 Directory Structure

### `notion/` - Notion MCP Integration
- **`test_real_notion.py`** - Test real Notion MCP server with your token
- **`notion_mcp_demo.py`** - Demo showing 18+ Notion tools automatically available
- **`real_notion_mcp_demo.py`** - Full Notion MCP integration example

### `tools/` - MCP Tool Examples
- **`hybrid_tool_demo.py`** - Combine MCP tools with local Python tools
- **`simple_interactive_demo.py`** - Interactive testing of MCP integration

### `integration/` - Advanced Integration Examples
- Coming soon: LLMgine + MCP integration examples

## 🎯 Quick Start

### 1. Test Real Notion Integration
```bash
cd demos/notion
export NOTION_TOKEN="your_token_here"
python test_real_notion.py
```

### 2. Run Tool Demos
```bash
cd demos/tools
python hybrid_tool_demo.py
python simple_interactive_demo.py
```

### 3. View Notion MCP Demo
```bash
cd demos/notion
python notion_mcp_demo.py
```

## 🔐 Environment Setup
```bash
# Set your Notion token
export NOTION_TOKEN="secret_your_token_here"

# Activate virtual environment
source ../.venv/bin/activate
```

## 📚 What Each Demo Shows

- **Notion Demos**: Real MCP server integration with 18+ professional tools
- **Tool Demos**: How to combine MCP tools with your own Python code
- **Integration Demos**: Advanced patterns for production use

## 🎉 Key Benefits Demonstrated

- ✅ **No custom API code needed** - Use existing MCP servers
- ✅ **18+ Notion tools automatically available** - Create, read, update, delete
- ✅ **Secure token handling** - Environment variables, no hardcoded secrets
- ✅ **Real-time integration** - Live connection to your Notion workspace
