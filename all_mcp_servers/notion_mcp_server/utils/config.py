"""
Configuration management for Notion MCP Server
"""

import config
import tools_for_mcp_server.config_mcp_tools_path as mcp_tool_path

# For NOTION config
notion_api_version = config.NOTION_API_VERSION
notion_base_url = config.NOTION_BASE_URL
notion_api_token = config.NOTION_API_TOKEN
notion_api_key = config.NOTION_API_KEY

# Directory path for Notion tools here
notion_tool_dir_path = mcp_tool_path.NOTION_TOOL_DIR_PATH

def get_notion_token():
    """Get Notion API token dynamically"""
    return notion_api_token or notion_api_key