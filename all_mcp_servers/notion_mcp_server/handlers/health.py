"""
Health handler for Notion MCP Server
"""

from typing import Any, Dict
import requests
from .base import BaseHandler
from ..utils.config import get_notion_token, notion_base_url

class HealthHandler(BaseHandler):
    """Handler for health check operations"""
    
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