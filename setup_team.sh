#!/bin/bash

# 🚀 Team Setup Script for MCP Integration
# Run this to get everything working on your machine

echo "🚀 Setting up MCP Integration Framework..."

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required but not installed"
    exit 1
fi

# Check if uv is installed
if ! command -v uv &> /dev/null; then
    echo "📦 Installing uv package manager..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    source ~/.bashrc 2>/dev/null || source ~/.zshrc 2>/dev/null
fi

# Create virtual environment if it doesn't exist
if [ ! -d ".venv" ]; then
    echo "🔧 Creating virtual environment..."
    uv venv
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source .venv/bin/activate

# Install dependencies
echo "📦 Installing dependencies..."
uv pip install -e ".[dev]"

# Check if Node.js is available for Notion MCP server
if command -v node &> /dev/null; then
    echo "✅ Node.js found - Notion MCP server ready"
    echo "📦 Installing Notion MCP server..."
    npm install -g @notionhq/notion-mcp-server
else
    echo "⚠️  Node.js not found - install it to use Notion MCP server"
    echo "   Visit: https://nodejs.org/"
fi

echo ""
echo "🎉 Setup complete! Here's what you can do next:"
echo ""
echo "1. Set your Notion token:"
echo "   export NOTION_TOKEN=\"your_token_here\""
echo ""
echo "2. Test the integration:"
echo "   cd demos/notion"
echo "   python test_real_notion.py"
echo ""
echo "3. Run other demos:"
echo "   cd demos/tools"
echo "   python hybrid_tool_demo.py"
echo ""
echo "📚 See demos/README.md for more examples!"
echo ""
echo "🚀 Happy MCP integrating!"
