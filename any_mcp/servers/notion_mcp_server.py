#!/usr/bin/env python3
"""
Notion MCP Server

A Model Context Protocol server that provides tools to interact with Notion workspaces.
Allows natural language queries to fetch data from Notion databases and pages.
"""

import asyncio
import os
import requests
from mcp.server.fastmcp import FastMCP
from typing import List, Dict, Any, Optional
import json

# Initialize the MCP server
mcp = FastMCP("NotionMCP", log_level="INFO")

# Notion configuration
NOTION_API_KEY = os.getenv("NOTION_API_KEY", "")
NOTION_VERSION = "2022-06-28"
NOTION_BASE_URL = "https://api.notion.com/v1"

# Validate API key is provided
if not NOTION_API_KEY:
    raise ValueError("NOTION_API_KEY environment variable is required. Please set it with your Notion integration key.")

def get_notion_headers():
    """Get standard headers for Notion API requests"""
    return {
        "Authorization": f"Bearer {NOTION_API_KEY}",
        "Notion-Version": NOTION_VERSION,
        "Content-Type": "application/json"
    }

@mcp.tool("health_check")
def health_check() -> str:
    """
    Health check for LLMGine integration and Notion API connectivity.
    
    Returns:
        JSON string with health status
    """
    try:
        # Test Notion API connectivity
        url = f"{NOTION_BASE_URL}/users/me"
        response = requests.get(url, headers=get_notion_headers())
        
        if response.status_code == 200:
            user_data = response.json()
            health_info = {
                "status": "healthy",
                "notion_api": "connected",
                "workspace": user_data.get("bot", {}).get("workspace_name", "unknown"),
                "message": "Notion MCP Server is healthy and ready for LLMGine integration"
            }
        else:
            health_info = {
                "status": "unhealthy",
                "notion_api": "error",
                "error": f"Notion API returned {response.status_code}",
                "message": "Notion API connection failed"
            }
        
        return json.dumps(health_info, indent=2)
        
    except Exception as e:
        health_info = {
            "status": "unhealthy",
            "notion_api": "error", 
            "error": str(e),
            "message": "Health check failed with exception"
        }
        return json.dumps(health_info, indent=2)

@mcp.tool("search_notion")
def search_notion(query: str = "", filter_type: str = "page_or_database") -> str:
    """
    Search across all accessible Notion content.
    
    Args:
        query: Search term (empty string returns all accessible content)
        filter_type: Type of content to search for ("page", "database", or "page_or_database")
    
    Returns:
        JSON string with search results
    """
    try:
        url = f"{NOTION_BASE_URL}/search"
        
        payload = {
            "query": query,
            "filter": {
                "value": filter_type,
                "property": "object"
            },
            "sort": {
                "direction": "descending",
                "timestamp": "last_edited_time"
            },
            "page_size": 10
        }
        
        response = requests.post(url, headers=get_notion_headers(), json=payload)
        
        if response.status_code == 200:
            data = response.json()
            return json.dumps(data, indent=2)
        else:
            error_msg = f"Error searching Notion: {response.status_code} {response.text}"
            return json.dumps({"error": error_msg}, indent=2)
            
    except Exception as e:
        error_msg = f"Exception during Notion search: {str(e)}"
        return json.dumps({"error": error_msg}, indent=2)

@mcp.tool("get_database_contents")
def get_database_contents(database_id: str, page_size: int = 100) -> str:
    """
    Get the contents of a specific Notion database.
    
    Args:
        database_id: The ID of the database to query
        page_size: Number of results to return (default: 100, max: 100)
    
    Returns:
        JSON string with database contents
    """
    try:
        url = f"{NOTION_BASE_URL}/databases/{database_id}/query"
        
        payload = {
            "page_size": min(page_size, 100)
        }
        
        response = requests.post(url, headers=get_notion_headers(), json=payload)
        
        if response.status_code == 200:
            data = response.json()
            return json.dumps(data, indent=2)
        else:
            error_msg = f"Error querying database: {response.status_code} {response.text}"
            return json.dumps({"error": error_msg}, indent=2)
            
    except Exception as e:
        error_msg = f"Exception during database query: {str(e)}"
        return json.dumps({"error": error_msg}, indent=2)

@mcp.tool("get_page_content")
def get_page_content(page_id: str) -> str:
    """
    Get the content of a specific Notion page.
    
    Args:
        page_id: The ID of the page to retrieve
    
    Returns:
        JSON string with page content
    """
    try:
        # Get page properties
        page_url = f"{NOTION_BASE_URL}/pages/{page_id}"
        page_response = requests.get(page_url, headers=get_notion_headers())
        
        if page_response.status_code != 200:
            error_msg = f"Error getting page: {page_response.status_code} {page_response.text}"
            return json.dumps({"error": error_msg}, indent=2)
        
        page_data = page_response.json()
        
        # Get page blocks (content)
        blocks_url = f"{NOTION_BASE_URL}/blocks/{page_id}/children"
        blocks_response = requests.get(blocks_url, headers=get_notion_headers())
        
        if blocks_response.status_code == 200:
            blocks_data = blocks_response.json()
            result = {
                "page": page_data,
                "blocks": blocks_data
            }
            return json.dumps(result, indent=2)
        else:
            # Return just page data if blocks can't be retrieved
            return json.dumps(page_data, indent=2)
            
    except Exception as e:
        error_msg = f"Exception during page retrieval: {str(e)}"
        return json.dumps({"error": error_msg}, indent=2)

@mcp.tool("get_task_tracker_tasks")
def get_task_tracker_tasks(status_filter: str = "all") -> str:
    """
    Get tasks from the Task Tracker database with optional status filtering.
    
    Args:
        status_filter: Filter by status ("all", "not_started", "in_progress", "done", etc.)
    
    Returns:
        JSON string with filtered tasks
    """
    try:
        # First, find the Task Tracker database
        search_url = f"{NOTION_BASE_URL}/search"
        search_payload = {
            "query": "Task Tracker",
            "filter": {
                "value": "database",
                "property": "object"
            }
        }
        
        search_response = requests.post(search_url, headers=get_notion_headers(), json=search_payload)
        
        if search_response.status_code != 200:
            return json.dumps({"error": f"Search failed: {search_response.status_code}"}, indent=2)
        
        search_data = search_response.json()
        
        # Find the Task Tracker database
        task_db = None
        for result in search_data.get("results", []):
            if result.get("object") == "database":
                title = ""
                if "title" in result and result["title"]:
                    title = result["title"][0].get("plain_text", "").lower()
                elif "properties" in result:
                    # Check if this looks like a task database
                    props = result["properties"].keys()
                    if any(prop.lower() in ["status", "task", "name"] for prop in props):
                        task_db = result
                        break
                
                if "task" in title or "tracker" in title:
                    task_db = result
                    break
        
        if not task_db:
            return json.dumps({"error": "Task Tracker database not found"}, indent=2)
        
        database_id = task_db["id"]
        
        # Query the database
        query_url = f"{NOTION_BASE_URL}/databases/{database_id}/query"
        query_payload = {"page_size": 100}
        
        # Add status filter if specified
        if status_filter != "all":
            # Try common status property names
            status_props = ["Status", "status", "State", "state"]
            db_props = task_db.get("properties", {})
            
            status_prop_name = None
            for prop_name in status_props:
                if prop_name in db_props:
                    status_prop_name = prop_name
                    break
            
            if status_prop_name:
                query_payload["filter"] = {
                    "property": status_prop_name,
                    "select": {
                        "equals": status_filter
                    }
                }
        
        response = requests.post(query_url, headers=get_notion_headers(), json=query_payload)
        
        if response.status_code == 200:
            data = response.json()
            
            # Simplify the response to show just the essential task info
            simplified_tasks = []
            for page in data.get("results", []):
                task = {
                    "id": page["id"],
                    "created_time": page.get("created_time"),
                    "last_edited_time": page.get("last_edited_time"),
                    "properties": {}
                }
                
                # Extract key properties
                for prop_name, prop_data in page.get("properties", {}).items():
                    if prop_data["type"] == "title":
                        task["properties"][prop_name] = prop_data["title"][0]["plain_text"] if prop_data["title"] else ""
                    elif prop_data["type"] == "select":
                        task["properties"][prop_name] = prop_data["select"]["name"] if prop_data["select"] else None
                    elif prop_data["type"] == "multi_select":
                        task["properties"][prop_name] = [item["name"] for item in prop_data["multi_select"]]
                    elif prop_data["type"] == "rich_text":
                        task["properties"][prop_name] = prop_data["rich_text"][0]["plain_text"] if prop_data["rich_text"] else ""
                    elif prop_data["type"] == "date":
                        task["properties"][prop_name] = prop_data["date"]["start"] if prop_data["date"] else None
                    elif prop_data["type"] == "checkbox":
                        task["properties"][prop_name] = prop_data["checkbox"]
                
                simplified_tasks.append(task)
            
            result = {
                "database_id": database_id,
                "total_tasks": len(simplified_tasks),
                "status_filter": status_filter,
                "tasks": simplified_tasks
            }
            
            return json.dumps(result, indent=2)
        else:
            error_msg = f"Error querying tasks: {response.status_code} {response.text}"
            return json.dumps({"error": error_msg}, indent=2)
            
    except Exception as e:
        error_msg = f"Exception during task retrieval: {str(e)}"
        return json.dumps({"error": error_msg}, indent=2)

if __name__ == "__main__":
    mcp.run()