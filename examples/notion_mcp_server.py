#!/usr/bin/env python3
"""
Example Notion MCP Server Implementation

This is a complete example of how to implement an MCP server that integrates with Notion.
Use this as a template for building your own MCP servers for different services.

Key Components Demonstrated:
1. MCP Server setup with proper JSON-RPC handling
2. Tool registration and discovery
3. Environment variable configuration
4. Error handling and logging
5. External API integration (Notion API)
6. Structured response formatting

Follow this pattern to create MCP servers for other services like:
- Slack, Discord, Teams
- Jira, Linear, GitHub Issues  
- Databases (PostgreSQL, MongoDB)
- Cloud services (AWS, GCP, Azure)
- Custom internal APIs

Installation:
    pip install requests python-dotenv

Usage:
    # Set environment variables
    export NOTION_API_TOKEN=your_notion_integration_token
    
    # Run as MCP server
    python examples/notion_mcp_server.py
    
    # Test with any-mcp-cli
    any-mcp-cli call --script examples/notion_mcp_server.py --tool search_notion --args query="project notes"
"""

import asyncio
import json
import logging
import os
import sys
from typing import Any, Dict, List, Optional
import traceback
import config
import requests

'''
    Load all of the config constants for this file below here
'''
# For NOTION config
notion_api_version = config.NOTION_API_VERSION
notion_base_url = config.NOTION_BASE_URL
notion_api_token = config.NOTION_API_TOKEN
notion_api_key = config.NOTION_API_KEY

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# External dependencies for Notion integration
try:
    import requests
    from dotenv import load_dotenv
except ImportError:
    print("Missing dependencies. Install with: pip install requests python-dotenv")
    sys.exit(1)

def get_notion_token():
    """Get Notion API token dynamically"""
    return notion_api_token or notion_api_key


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
        self.tools = [
            {
                "name": "search_notion",
                "description": "Search across all Notion content you have access to",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Search query to find content"
                        },
                        "filter_type": {
                            "type": "string",
                            "enum": ["page", "database"],
                            "description": "Filter results by type (optional)"
                        }
                    },
                    "required": ["query"]
                }
            },
            {
                "name": "get_page_content",
                "description": "Retrieve the content of a specific Notion page",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "page_id": {
                            "type": "string",
                            "description": "The ID of the page to retrieve"
                        }
                    },
                    "required": ["page_id"]
                }
            },
            {
                "name": "get_database_contents",
                "description": "Get all entries from a Notion database",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "database_id": {
                            "type": "string",
                            "description": "The ID of the database to query"
                        },
                        "filter_property": {
                            "type": "string",
                            "description": "Property name to filter by (optional)"
                        },
                        "filter_value": {
                            "type": "string", 
                            "description": "Value to filter for (optional)"
                        }
                    },
                    "required": ["database_id"]
                }
            },
            {
                "name": "create_page",
                "description": "Create a new page in Notion",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "parent_id": {
                            "type": "string",
                            "description": "ID of parent page or database"
                        },
                        "title": {
                            "type": "string",
                            "description": "Title of the new page"
                        },
                        "content": {
                            "type": "string",
                            "description": "Text content for the page (optional)"
                        }
                    },
                    "required": ["parent_id", "title"]
                }
            },
            {
                "name": "update_page",
                "description": "Update an existing Notion page",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "page_id": {
                            "type": "string",
                            "description": "ID of the page to update"
                        },
                        "title": {
                            "type": "string",
                            "description": "New title (optional)"
                        },
                        "properties": {
                            "type": "object",
                            "description": "Properties to update (optional)"
                        }
                    },
                    "required": ["page_id"]
                }
            },
            {
                "name": "delete_page",
                "description": "Delete a Notion page",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "page_id": {
                            "type": "string",
                            "description": "ID of the page to delete"
                        }
                    },
                    "required": ["page_id"]
                }
            },
            {
                "name": "move_page",
                "description": "Move a page to a different parent",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "page_id": {
                            "type": "string",
                            "description": "ID of the page to move"
                        },
                        "new_parent_id": {
                            "type": "string",
                            "description": "ID of the new parent page or database"
                        }
                    },
                    "required": ["page_id", "new_parent_id"]
                }
            },
            {
                "name": "create_database",
                "description": "Create a new Notion database",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "parent_id": {
                            "type": "string",
                            "description": "ID of parent page or database"
                        },
                        "title": {
                            "type": "string",
                            "description": "Title of the database"
                        },
                        "properties": {
                            "type": "object",
                            "description": "Database properties schema"
                        }
                    },
                    "required": ["parent_id", "title"]
                }
            },
            {
                "name": "update_database",
                "description": "Update an existing Notion database",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "database_id": {
                            "type": "string",
                            "description": "ID of the database to update"
                        },
                        "title": {
                            "type": "string",
                            "description": "New title (optional)"
                        },
                        "properties": {
                            "type": "object",
                            "description": "Properties to update (optional)"
                        }
                    },
                    "required": ["database_id"]
                }
            },
            {
                "name": "delete_database",
                "description": "Delete a Notion database",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "database_id": {
                            "type": "string",
                            "description": "ID of the database to delete"
                        }
                    },
                    "required": ["database_id"]
                }
            },
            {
                "name": "query_database",
                "description": "Advanced database query with filters and sorting",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "database_id": {
                            "type": "string",
                            "description": "ID of the database to query"
                        },
                        "filter": {
                            "type": "object",
                            "description": "Filter criteria (optional)"
                        },
                        "sorts": {
                            "type": "array",
                            "description": "Sorting criteria (optional)"
                        },
                        "page_size": {
                            "type": "integer",
                            "description": "Number of results per page (optional)"
                        }
                    },
                    "required": ["database_id"]
                }
            },
            {
                "name": "create_block",
                "description": "Create a new content block in a page",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "page_id": {
                            "type": "string",
                            "description": "ID of the page to add block to"
                        },
                        "block_type": {
                            "type": "string",
                            "enum": ["paragraph", "heading_1", "heading_2", "heading_3", "bulleted_list_item", "numbered_list_item", "to_do", "toggle", "code", "quote", "callout", "divider", "image", "video", "file", "pdf", "bookmark", "equation", "table_of_contents", "breadcrumb", "link_preview", "template_button", "synced_block", "column_list", "column", "table", "table_row", "embed", "equation", "link_to_page", "audio", "unsupported"],
                            "description": "Type of block to create"
                        },
                        "content": {
                            "type": "string",
                            "description": "Text content for the block"
                        }
                    },
                    "required": ["page_id", "block_type", "content"]
                }
            },
            {
                "name": "update_block",
                "description": "Update an existing content block",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "block_id": {
                            "type": "string",
                            "description": "ID of the block to update"
                        },
                        "content": {
                            "type": "string",
                            "description": "New content for the block"
                        }
                    },
                    "required": ["block_id", "content"]
                }
            },
            {
                "name": "delete_block",
                "description": "Delete a content block",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "block_id": {
                            "type": "string",
                            "description": "ID of the block to delete"
                        }
                    },
                    "required": ["block_id"]
                }
            },
            {
                "name": "get_block_children",
                "description": "Get all child blocks of a page or block",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "block_id": {
                            "type": "string",
                            "description": "ID of the page or block"
                        },
                        "page_size": {
                            "type": "integer",
                            "description": "Number of results per page (optional)"
                        }
                    },
                    "required": ["block_id"]
                }
            },
            {
                "name": "append_block_children",
                "description": "Add multiple blocks to a page or block",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "block_id": {
                            "type": "string",
                            "description": "ID of the page or block to add to"
                        },
                        "blocks": {
                            "type": "array",
                            "description": "Array of block objects to add"
                        }
                    },
                    "required": ["block_id", "blocks"]
                }
            },
            {
                "name": "get_user",
                "description": "Get information about a specific user",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "user_id": {
                            "type": "string",
                            "description": "ID of the user to retrieve"
                        }
                    },
                    "required": ["user_id"]
                }
            },
            {
                "name": "get_users",
                "description": "Get list of all users in the workspace",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "page_size": {
                            "type": "integer",
                            "description": "Number of results per page (optional)"
                        }
                    },
                    "required": []
                }
            },
            {
                "name": "get_me",
                "description": "Get information about the current user",
                "inputSchema": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            },
            {
                "name": "create_comment",
                "description": "Create a comment on a page or block",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "parent_id": {
                            "type": "string",
                            "description": "ID of the page or block to comment on"
                        },
                        "content": {
                            "type": "string",
                            "description": "Comment text content"
                        }
                    },
                    "required": ["parent_id", "content"]
                }
            },
            {
                "name": "get_comments",
                "description": "Get all comments for a page or block",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "block_id": {
                            "type": "string",
                            "description": "ID of the page or block"
                        },
                        "page_size": {
                            "type": "integer",
                            "description": "Number of results per page (optional)"
                        }
                    },
                    "required": ["block_id"]
                }
            },
            {
                "name": "upload_file",
                "description": "Upload a file to Notion",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "page_id": {
                            "type": "string",
                            "description": "ID of the page to upload to"
                        },
                        "file_path": {
                            "type": "string",
                            "description": "Path to the file to upload"
                        },
                        "caption": {
                            "type": "string",
                            "description": "Caption for the file (optional)"
                        }
                    },
                    "required": ["page_id", "file_path"]
                }
            },
            {
                "name": "search_with_filters",
                "description": "Advanced search with multiple filters and options",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Search query string"
                        },
                        "filter": {
                            "type": "object",
                            "description": "Complex filter object (optional)"
                        },
                        "sort": {
                            "type": "object",
                            "description": "Sorting criteria (optional)"
                        },
                        "page_size": {
                            "type": "integer",
                            "description": "Number of results per page (optional)"
                        }
                    },
                    "required": ["query"]
                }
            },
            {
                "name": "health_check",
                "description": "Check if the Notion MCP server is healthy and can connect to Notion API",
                "inputSchema": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            }
        ]
    
    def get_notion_headers(self) -> Dict[str, str]:
        """Get standard headers for Notion API requests."""
        token = get_notion_token()
        if not token:
            raise ValueError("NOTION_API_TOKEN not configured")
        return {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Notion-Version": notion_api_version
        }
    
    async def search_notion(self, query: str, filter_type: Optional[str] = None) -> Dict[str, Any]:
        """
        Search Notion content.
        
        Args:
            query: Search query string
            filter_type: Optional filter by 'page' or 'database'
            
        Returns:
            Dict containing search results
        """
        token = get_notion_token()
        if not token:
            return {"error": "NOTION_API_TOKEN not configured"}
        
        try:
            url = f"{notion_base_url}/search"
            payload = {
                "query": query,
                "page_size": 100  # Increased from 20 to 100 for more comprehensive results
            }
            
            if filter_type:
                payload["filter"] = {"value": filter_type, "property": "object"}
            
            response = requests.post(
                url,
                headers=self.get_notion_headers(),
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                results = []
                for item in data.get("results", []):
                    result = {
                        "id": item["id"],
                        "type": item["object"],
                        "url": item.get("url", ""),
                        "title": self._extract_title(item),
                        "last_edited": item.get("last_edited_time", "")
                    }
                    results.append(result)
                
                return {
                    "success": True,
                    "query": query,
                    "results_count": len(results),
                    "results": results
                }
            else:
                return {
                    "error": f"Notion API error: {response.status_code}",
                    "details": response.text
                }
                
        except Exception as e:
            return {"error": f"Search failed: {str(e)}"}
    
    async def get_page_content(self, page_id: str) -> Dict[str, Any]:
        """
        Get content of a specific Notion page.
        
        Args:
            page_id: The Notion page ID
            
        Returns:
            Dict containing page content
        """
        token = get_notion_token()
        if not token:
            return {"error": "NOTION_API_TOKEN not configured"}
        
        try:
            # Get page metadata
            page_url = f"{notion_base_url}/pages/{page_id}"
            page_response = requests.get(
                page_url,
                headers=self.get_notion_headers(),
                timeout=30
            )
            
            if page_response.status_code != 200:
                return {
                    "error": f"Failed to get page: {page_response.status_code}",
                    "details": page_response.text
                }
            
            page_data = page_response.json()
            
            # Get page blocks (content)
            blocks_url = f"{notion_base_url}/blocks/{page_id}/children"
            blocks_response = requests.get(
                blocks_url,
                headers=self.get_notion_headers(),
                timeout=30
            )
            
            blocks_data = blocks_response.json() if blocks_response.status_code == 200 else {"results": []}
            
            return {
                "success": True,
                "page_id": page_id,
                "title": self._extract_title(page_data),
                "url": page_data.get("url", ""),
                "last_edited": page_data.get("last_edited_time", ""),
                "content_blocks": len(blocks_data.get("results", [])),
                "blocks": blocks_data.get("results", [])
            }
            
        except Exception as e:
            return {"error": f"Failed to get page content: {str(e)}"}
    
    async def get_database_contents(self, database_id: str, filter_property: Optional[str] = None, 
                                  filter_value: Optional[str] = None) -> Dict[str, Any]:
        """
        Get contents of a Notion database.
        
        Args:
            database_id: The Notion database ID
            filter_property: Optional property name to filter by
            filter_value: Optional value to filter for
            
        Returns:
            Dict containing database contents
        """
        token = get_notion_token()
        if not token:
            return {"error": "NOTION_API_TOKEN not configured"}
        
        try:
            url = f"{notion_base_url}/databases/{database_id}/query"
            payload = {"page_size": 50}
            
            # Add filter if specified
            if filter_property and filter_value:
                payload["filter"] = {
                    "property": filter_property,
                    "rich_text": {
                        "contains": filter_value
                    }
                }
            
            response = requests.post(
                url,
                headers=self.get_notion_headers(),
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                entries = []
                
                for item in data.get("results", []):
                    entry = {
                        "id": item["id"],
                        "url": item.get("url", ""),
                        "title": self._extract_title(item),
                        "last_edited": item.get("last_edited_time", ""),
                        "properties": self._extract_properties(item.get("properties", {}))
                    }
                    entries.append(entry)
                
                return {
                    "success": True,
                    "database_id": database_id,
                    "entries_count": len(entries),
                    "entries": entries
                }
            else:
                return {
                    "error": f"Database query failed: {response.status_code}",
                    "details": response.text
                }
                
        except Exception as e:
            return {"error": f"Failed to get database contents: {str(e)}"}
    
    async def create_page(self, parent_id: str, title: str, content: Optional[str] = None) -> Dict[str, Any]:
        """
        Create a new page in Notion.
        
        Args:
            parent_id: ID of parent page or database
            title: Title of the new page
            content: Optional text content
            
        Returns:
            Dict containing creation result
        """
        token = get_notion_token()
        if not token:
            return {"error": "NOTION_API_TOKEN not configured"}
        
        try:
            url = f"{notion_base_url}/pages"
            payload = {
                "parent": {"page_id": parent_id},
                "properties": {
                    "title": {
                        "title": [
                            {
                                "text": {
                                    "content": title
                                }
                            }
                        ]
                    }
                }
            }
            
            # Add content if provided
            if content:
                payload["children"] = [
                    {
                        "object": "block",
                        "type": "paragraph",
                        "paragraph": {
                            "rich_text": [
                                {
                                    "type": "text",
                                    "text": {
                                        "content": content
                                    }
                                }
                            ]
                        }
                    }
                ]
            
            response = requests.post(
                url,
                headers=self.get_notion_headers(),
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                page_data = response.json()
                return {
                    "success": True,
                    "page_id": page_data["id"],
                    "url": page_data.get("url", ""),
                    "title": title
                }
            else:
                return {
                    "error": f"Page creation failed: {response.status_code}",
                    "details": response.text
                }
                
        except Exception as e:
            return {"error": f"Failed to create page: {str(e)}"}
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Check server health and Notion API connectivity.
        
        Returns:
            Dict containing health status
        """
        token = get_notion_token()
        if not token:
            return {
                "healthy": False,
                "error": "NOTION_API_TOKEN not configured",
                "suggestion": "Set NOTION_API_TOKEN environment variable"
            }
        
        try:
            # Test API connectivity
            url = f"{notion_base_url}/users/me"
            response = requests.get(
                url,
                headers=self.get_notion_headers(),
                timeout=10
            )
            
            if response.status_code == 200:
                user_data = response.json()
                return {
                    "healthy": True,
                    "notion_api": "connected",
                    "user_id": user_data.get("id", "unknown"),
                    "user_name": user_data.get("name", "unknown")
                }
            else:
                return {
                    "healthy": False,
                    "notion_api": "error",
                    "status_code": response.status_code,
                    "error": response.text
                }
                
        except Exception as e:
            return {
                "healthy": False,
                "error": f"Health check failed: {str(e)}"
            }
    
    def _extract_title(self, item: Dict[str, Any]) -> str:
        """Extract title from a Notion object."""
        if "properties" in item:
            # Database entry
            for prop_name, prop_data in item["properties"].items():
                if prop_data.get("type") == "title":
                    title_array = prop_data.get("title", [])
                    if title_array:
                        return "".join([t.get("plain_text", "") for t in title_array])
        
        # Page object
        if "title" in item:
            title_array = item.get("title", [])
            if title_array:
                return "".join([t.get("plain_text", "") for t in title_array])
        
        return "Untitled"
    
    def _extract_properties(self, properties: Dict[str, Any]) -> Dict[str, Any]:
        """Extract simplified properties from Notion properties object."""
        simplified = {}
        
        for name, prop in properties.items():
            prop_type = prop.get("type", "unknown")
            
            if prop_type == "title":
                title_array = prop.get("title", [])
                simplified[name] = "".join([t.get("plain_text", "") for t in title_array])
            elif prop_type == "rich_text":
                text_array = prop.get("rich_text", [])
                simplified[name] = "".join([t.get("plain_text", "") for t in text_array])
            elif prop_type == "select":
                select_obj = prop.get("select")
                simplified[name] = select_obj.get("name", "") if select_obj else ""
            elif prop_type == "multi_select":
                multi_select = prop.get("multi_select", [])
                simplified[name] = [item.get("name", "") for item in multi_select]
            elif prop_type == "date":
                date_obj = prop.get("date")
                simplified[name] = date_obj.get("start", "") if date_obj else ""
            elif prop_type == "checkbox":
                simplified[name] = prop.get("checkbox", False)
            elif prop_type == "number":
                simplified[name] = prop.get("number", 0)
            else:
                simplified[name] = f"[{prop_type}]"
        
        return simplified

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


async def main():
    """
    Main server loop - handles stdin/stdout communication for MCP protocol.
    
    This is the standard pattern for MCP servers:
    1. Read JSON-RPC messages from stdin
    2. Process through handle_request
    3. Write responses to stdout
    """
    server = NotionMCPServer()
    
    logger.info("Notion MCP Server starting...")
    token = get_notion_token()
    logger.info(f"Notion API configured: {'Yes' if token else 'No'}")
    
    while True:
        try:
            # Read a line from stdin
            line = await asyncio.get_event_loop().run_in_executor(None, sys.stdin.readline)
            
            if not line:
                break
                
            line = line.strip()
            if not line:
                continue
            
            # Parse JSON-RPC message
            try:
                message = json.loads(line)
            except json.JSONDecodeError as e:
                logger.error(f"Invalid JSON received: {e}")
                continue
            
            # Handle the request
            response = await server.handle_request(message)
            
            # Send response
            print(json.dumps(response), flush=True)
            
        except KeyboardInterrupt:
            logger.info("Server shutting down...")
            break
        except Exception as e:
            logger.error(f"Server error: {e}")
            logger.error(traceback.format_exc())


if __name__ == "__main__":
    asyncio.run(main())
