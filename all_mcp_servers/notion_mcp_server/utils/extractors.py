"""
Data extraction utilities for Notion objects
"""

from typing import Any, Dict

def extract_title(item: Dict[str, Any]) -> str:
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

def extract_properties(properties: Dict[str, Any]) -> Dict[str, Any]:
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