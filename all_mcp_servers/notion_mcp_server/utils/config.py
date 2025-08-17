"""
Configuration management for Notion MCP Server
"""

import config as global_config
from tools_for_mcp_server import config_mcp_tools_path as mcp_tool_path

# For NOTION config
notion_api_version = global_config.NOTION_API_VERSION
notion_base_url = global_config.NOTION_BASE_URL
notion_api_token = global_config.NOTION_API_TOKEN
notion_api_key = global_config.NOTION_API_KEY

# Directory path for Notion tools here
notion_tool_dir_path = mcp_tool_path.NOTION_TOOL_DIR_PATH

def get_notion_token():
    """Get Notion API token dynamically"""
    return notion_api_token or notion_api_key