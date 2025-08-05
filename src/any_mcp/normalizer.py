"""
MCP Normalizer - Standardizes results from different MCP servers.
"""

from typing import Any, Dict


class MCPNormalizer:
    """
    Normalizes results from different MCP servers into a standard format.
    """
    
    def normalize_result(self, result: Any) -> Any:
        """
        Normalize a result from an MCP tool.
        
        Args:
            result: The raw result from the MCP tool
            
        Returns:
            The normalized result
        """
        # For now, just return the result as-is
        # In a real implementation, this would:
        # 1. Handle different response formats
        # 2. Convert errors to standard format
        # 3. Validate response schemas
        # 4. Add metadata (timing, source MCP, etc.)
        
        return result
    
    def normalize_error(self, error: Any) -> Dict[str, Any]:
        """
        Normalize an error from an MCP tool.
        
        Args:
            error: The raw error from the MCP tool
            
        Returns:
            The normalized error
        """
        # Standardize error format
        if isinstance(error, dict):
            return {
                "error": True,
                "code": error.get("code", 500),
                "message": error.get("message", "Unknown error"),
                "data": error.get("data")
            }
        elif isinstance(error, Exception):
            return {
                "error": True,
                "code": 500,
                "message": str(error),
                "data": None
            }
        else:
            return {
                "error": True,
                "code": 500,
                "message": "Unknown error occurred",
                "data": error
            } 