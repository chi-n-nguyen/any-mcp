"""
Databases handler for Notion MCP Server
"""

from typing import Any, Dict, Optional
import requests
from .base import BaseHandler
from ..utils.config import get_notion_token, notion_base_url
from ..utils.extractors import extract_title, extract_properties

class DatabasesHandler(BaseHandler):
    """Handler for database operations"""
    
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
                        "title": extract_title(item),
                        "last_edited": item.get("last_edited_time", ""),
                        "properties": extract_properties(item.get("properties", {}))
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