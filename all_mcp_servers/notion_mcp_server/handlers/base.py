"""
Base handler class for common functionality
"""

from ..utils.notion_client import NotionClient

class BaseHandler:
    """Base class for all handlers"""
    
    def __init__(self):
        self.notion_client = NotionClient()
    
    def get_notion_headers(self):
        """Get standard headers for Notion API requests."""
        return self.notion_client.get_notion_headers()