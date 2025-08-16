"""
Search handler for Notion MCP Server
"""

from typing import Any, Dict, Optional
import requests
from .base import BaseHandler
from ..utils.config import get_notion_token, notion_base_url
from ..utils.extractors import extract_title

class SearchHandler(BaseHandler):
    """Handler for search operations"""
    
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
                        "title": extract_title(item),
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