"""
Pages handler for Notion MCP Server
"""

from typing import Any, Dict, Optional
import requests
from .base import BaseHandler
from ..utils.config import get_notion_token, notion_base_url
from ..utils.extractors import extract_title

class PagesHandler(BaseHandler):
    """Handler for page operations"""
    
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
                "title": extract_title(page_data),
                "url": page_data.get("url", ""),
                "last_edited": page_data.get("last_edited_time", ""),
                "content_blocks": len(blocks_data.get("results", [])),
                "blocks": blocks_data.get("results", [])
            }
            
        except Exception as e:
            return {"error": f"Failed to get page content: {str(e)}"}
    
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