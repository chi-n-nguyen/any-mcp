#!/bin/bash
# Notion MCP Server Launcher for LLMGine Integration
# This script sets up the environment and launches the Notion MCP server

# Set the Notion API key (must be provided via environment variable)
if [ -z "$NOTION_API_KEY" ]; then
    echo "Error: NOTION_API_KEY environment variable is required"
    echo "Please set it with: export NOTION_API_KEY=your_notion_api_key"
    exit 1
fi

# Set log level 
export LOG_LEVEL="${LOG_LEVEL:-INFO}"

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Change to the script directory
cd "$SCRIPT_DIR"

# Check if virtual environment exists and activate it
if [ -d ".venv" ]; then
    source .venv/bin/activate
fi

# Launch the Notion MCP server
exec python3 notion_mcp_server.py "$@"
