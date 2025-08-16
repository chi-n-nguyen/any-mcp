'''
    Setup structure for future implementation with discord
'''
import config

# For loading tool path --> then load all tools for notion
import tools_for_mcp_server.config_mcp_tools_path as mcp_tool_path
from tools_for_mcp_server.tool_mcp_server_loading_package.load_tools import load_all_tools

# Load the constant for discord tool path here
discord_tool_dir_path = mcp_tool_path.DISCORD_TOOL_DIR_PATH