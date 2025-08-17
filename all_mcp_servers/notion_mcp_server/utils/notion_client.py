"""
Notion API client wrapper
"""

from typing import Dict
import requests
from .config import get_notion_token, notion_api_version

class NotionClient:
    """Wrapper for Notion API requests"""
    
    def __init__(self):
        pass
    
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