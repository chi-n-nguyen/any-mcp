"""
Main Notion MCP Server class
"""

import json
import logging
import traceback
from typing import Any, Dict
from tools_for_mcp_server.tool_mcp_server_loading_package.load_tools import load_all_tools
from .utils.config import notion_tool_dir_path
from .handlers import SearchHandler, PagesHandler, DatabasesHandler, HealthHandler

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class NotionMCPServer:
    """
    Example MCP Server for Notion integration.
    
    This class demonstrates the standard pattern for building MCP servers:
    1. Tool registration in __init__
    2. JSON-RPC message handling
    3. Tool execution with proper error handling
    4. External API integration
    """
    
    def __init__(self):
        """Initialize the server and register available tools."""
        self.tools = load_all_tools(notion_tool_dir_path)
        
        # Initialize handlers
        self.search_handler = SearchHandler()
        self.pages_handler = PagesHandler()
        self.databases_handler = DatabasesHandler()
        self.health_handler = HealthHandler()
    
    async def search_notion(self, query: str, filter_type: str = None) -> Dict[str, Any]:
        """
        Search Notion content.
        
        Args:
            query: Search query string
            filter_type: Optional filter by 'page' or 'database'
            
        Returns:
            Dict containing search results
        """
        return await self.search_handler.search_notion(query, filter_type)
    
    async def get_page_content(self, page_id: str) -> Dict[str, Any]:
        """
        Get content of a specific Notion page.
        
        Args:
            page_id: The Notion page ID
            
        Returns:
            Dict containing page content
        """
        return await self.pages_handler.get_page_content(page_id)
    
    async def get_database_contents(self, database_id: str, filter_property: str = None, 
                                  filter_value: str = None) -> Dict[str, Any]:
        """
        Get contents of a Notion database.
        
        Args:
            database_id: The Notion database ID
            filter_property: Optional property name to filter by
            filter_value: Optional value to filter for
            
        Returns:
            Dict containing database contents
        """
        return await self.databases_handler.get_database_contents(database_id, filter_property, filter_value)
    
    async def create_page(self, parent_id: str, title: str, content: str = None) -> Dict[str, Any]:
        """
        Create a new page in Notion.
        
        Args:
            parent_id: ID of parent page or database
            title: Title of the new page
            content: Optional text content
            
        Returns:
            Dict containing creation result
        """
        return await self.pages_handler.create_page(parent_id, title, content)
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Check server health and Notion API connectivity.
        
        Returns:
            Dict containing health status
        """
        return await self.health_handler.health_check()

    async def handle_request(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle incoming JSON-RPC requests.
        
        This is the main entry point for MCP protocol messages.
        """
        try:
            method = message.get("method")
            params = message.get("params", {})
            request_id = message.get("id")
            
            if method == "initialize":
                return {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "result": {
                        "protocolVersion": "2024-11-05",
                        "capabilities": {
                            "tools": {}
                        },
                        "serverInfo": {
                            "name": "notion-mcp-server",
                            "version": "1.0.0"
                        }
                    }
                }
            
            elif method == "tools/list":
                return {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "result": {
                        "tools": self.tools
                    }
                }
            
            elif method == "tools/call":
                tool_name = params.get("name")
                arguments = params.get("arguments", {})
                
                # Route to appropriate tool handler
                if tool_name == "search_notion":
                    result = await self.search_notion(
                        arguments.get("query", ""),
                        arguments.get("filter_type")
                    )
                elif tool_name == "get_page_content":
                    result = await self.get_page_content(arguments.get("page_id", ""))
                elif tool_name == "get_database_contents":
                    result = await self.get_database_contents(
                        arguments.get("database_id", ""),
                        arguments.get("filter_property"),
                        arguments.get("filter_value")
                    )
                elif tool_name == "create_page":
                    result = await self.create_page(
                        arguments.get("parent_id", ""),
                        arguments.get("title", ""),
                        arguments.get("content")
                    )
                elif tool_name == "health_check":
                    result = await self.health_check()
                else:
                    return {
                        "jsonrpc": "2.0",
                        "id": request_id,
                        "error": {
                            "code": -32601,
                            "message": f"Unknown tool: {tool_name}"
                        }
                    }
                
                return {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "result": {
                        "content": [
                            {
                                "type": "text",
                                "text": json.dumps(result, indent=2)
                            }
                        ]
                    }
                }
            
            else:
                return {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "error": {
                        "code": -32601,
                        "message": f"Unknown method: {method}"
                    }
                }
                
        except Exception as e:
            logger.error(f"Error handling request: {e}")
            logger.error(traceback.format_exc())
            return {
                "jsonrpc": "2.0",
                "id": message.get("id"),
                "error": {
                    "code": -32603,
                    "message": f"Internal error: {str(e)}"
                }
            }