# Tools for MCP Servers

This directory serves as a centralized repository for tools used by various Multi-Cloud Platform (MCP) servers. Each subdirectory within `tools_for_mcp_server` is dedicated to a specific MCP server, containing its associated tools in JSON format.

## Structure

- `tools_for_mcp_server/`:
  - `[mcp_server_name]_mcp_server_tools/`:
    - `tool_name.json`: Each JSON file defines a specific tool.
  - `config_mcp_tools_path.py`: Defines constants for the directory paths of each MCP server's tools, ensuring a clear and organized code structure.
  - `tool_mcp_server_loading_package/`:
    - `load_tools.py`: Contains a function to dynamically load all JSON-defined tools for a given MCP server directory into a list of dictionaries.

## Usage

Tools defined in this directory, such as those for Notion (`tools_for_mcp_server/notion_mcp_server_tools/`), are utilized by example MCP server implementations, like `examples/discord_mcp_server.py`, and other future integrations.

The `load_tools.py` module provides a utility function that takes a directory path (e.g., `tools_for_mcp_server/notion_mcp_server_tools`) as an input argument. This function reads all JSON files within the specified directory and returns their contents as a list of dictionaries, making the tools readily available for use by MCP servers. 