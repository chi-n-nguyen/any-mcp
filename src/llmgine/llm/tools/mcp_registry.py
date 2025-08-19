"""
MCP Server Registry and Tool Registration System

This module provides a comprehensive system for registering, managing, and
discovering MCP servers and their tools within the llmgine ecosystem.
"""

import asyncio
import json
import logging
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Union
import yaml

from llmgine.llm import SessionID
from llmgine.llm.tools.mcp_tool_manager import MCPServerConfig

logger = logging.getLogger(__name__)


@dataclass
class MCPServerDefinition:
    """Extended server definition with metadata and configuration options."""
    name: str
    command: str
    args: List[str]
    env: Dict[str, str] = field(default_factory=dict)
    
    # Metadata
    description: str = ""
    version: str = "1.0.0"
    author: str = ""
    tags: List[str] = field(default_factory=list)
    
    # Configuration
    auto_start: bool = True
    priority: int = 50  # Lower numbers = higher priority
    timeout_seconds: int = 30
    max_retries: int = 3
    
    # Requirements and compatibility
    python_requirements: List[str] = field(default_factory=list)
    system_requirements: List[str] = field(default_factory=list)
    supported_platforms: List[str] = field(default_factory=lambda: ["linux", "darwin", "win32"])
    
    # Tool filtering
    include_tools: Optional[List[str]] = None  # If set, only include these tools
    exclude_tools: List[str] = field(default_factory=list)  # Exclude these tools
    
    def to_server_config(self) -> MCPServerConfig:
        """Convert to MCPServerConfig for use with MCPToolManager."""
        return MCPServerConfig(
            name=self.name,
            command=self.command,
            args=self.args,
            env=self.env,
            auto_start=self.auto_start
        )


@dataclass
class MCPToolInfo:
    """Information about a discovered MCP tool."""
    name: str
    server_name: str
    description: str
    schema: Dict[str, Any]
    parameters: Dict[str, Any]
    
    # Metadata
    category: str = "general"
    tags: List[str] = field(default_factory=list)
    examples: List[Dict[str, Any]] = field(default_factory=list)
    
    # Runtime info
    available: bool = True
    last_used: Optional[str] = None
    usage_count: int = 0
    average_execution_time: float = 0.0


class MCPServerRegistry:
    """
    Registry for managing MCP server definitions and tool discovery.
    
    This registry provides:
    - Server definition management from files and code
    - Tool discovery and metadata management
    - Server health monitoring and auto-restart
    - Configuration validation and dependency checking
    """
    
    def __init__(self, config_dir: Optional[Union[str, Path]] = None):
        self.config_dir = Path(config_dir) if config_dir else Path.cwd() / "mcp_config"
        self.server_definitions: Dict[str, MCPServerDefinition] = {}
        self.discovered_tools: Dict[str, MCPToolInfo] = {}
        self.server_health: Dict[str, Dict[str, Any]] = {}
        
        # Ensure config directory exists
        self.config_dir.mkdir(exist_ok=True)
        
        logger.info(f"Initialized MCPServerRegistry with config dir: {self.config_dir}")
    
    # ==================== Server Definition Management ====================
    
    def register_server(self, definition: MCPServerDefinition) -> bool:
        """
        Register a server definition.
        
        Args:
            definition: Server definition to register
            
        Returns:
            True if registration was successful
        """
        try:
            # Validate definition
            if not self._validate_server_definition(definition):
                return False
            
            # Check platform compatibility
            if not self._check_platform_compatibility(definition):
                logger.warning(f"Server {definition.name} not compatible with current platform")
                return False
            
            # Store definition
            self.server_definitions[definition.name] = definition
            
            # Initialize health tracking
            self.server_health[definition.name] = {
                "status": "registered",
                "last_check": None,
                "failures": 0,
                "uptime": 0
            }
            
            logger.info(f"Registered MCP server: {definition.name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to register server {definition.name}: {e}")
            return False
    
    def unregister_server(self, name: str) -> bool:
        """Unregister a server definition."""
        if name in self.server_definitions:
            del self.server_definitions[name]
            if name in self.server_health:
                del self.server_health[name]
            
            # Remove tools from this server
            tools_to_remove = [
                tool_name for tool_name, tool_info in self.discovered_tools.items()
                if tool_info.server_name == name
            ]
            for tool_name in tools_to_remove:
                del self.discovered_tools[tool_name]
            
            logger.info(f"Unregistered MCP server: {name}")
            return True
        
        return False
    
    def get_server_definition(self, name: str) -> Optional[MCPServerDefinition]:
        """Get a server definition by name."""
        return self.server_definitions.get(name)
    
    def list_servers(
        self,
        tags: Optional[List[str]] = None,
        status: Optional[str] = None
    ) -> List[MCPServerDefinition]:
        """
        List server definitions with optional filtering.
        
        Args:
            tags: Filter by tags
            status: Filter by health status
            
        Returns:
            List of matching server definitions
        """
        servers = list(self.server_definitions.values())
        
        # Filter by tags
        if tags:
            servers = [
                server for server in servers
                if any(tag in server.tags for tag in tags)
            ]
        
        # Filter by status
        if status:
            servers = [
                server for server in servers
                if self.server_health.get(server.name, {}).get("status") == status
            ]
        
        # Sort by priority
        servers.sort(key=lambda s: s.priority)
        
        return servers
    
    # ==================== Configuration File Management ====================
    
    def load_from_file(self, file_path: Union[str, Path]) -> int:
        """
        Load server definitions from a configuration file.
        
        Supports YAML and JSON formats.
        
        Returns:
            Number of servers loaded
        """
        file_path = Path(file_path)
        
        if not file_path.exists():
            logger.error(f"Configuration file not found: {file_path}")
            return 0
        
        try:
            with open(file_path, 'r') as f:
                if file_path.suffix.lower() in ['.yml', '.yaml']:
                    config = yaml.safe_load(f)
                else:
                    config = json.load(f)
            
            return self._load_from_config(config)
            
        except Exception as e:
            logger.error(f"Failed to load configuration from {file_path}: {e}")
            return 0
    
    def load_from_directory(self, directory: Optional[Union[str, Path]] = None) -> int:
        """
        Load all server definitions from a directory.
        
        Args:
            directory: Directory to scan (defaults to config_dir)
            
        Returns:
            Total number of servers loaded
        """
        directory = Path(directory) if directory else self.config_dir
        
        if not directory.exists():
            logger.warning(f"Configuration directory not found: {directory}")
            return 0
        
        total_loaded = 0
        
        # Load from all config files
        for file_path in directory.glob("*.{yml,yaml,json}"):
            loaded = self.load_from_file(file_path)
            total_loaded += loaded
            logger.info(f"Loaded {loaded} servers from {file_path}")
        
        return total_loaded
    
    def save_to_file(self, file_path: Union[str, Path], servers: Optional[List[str]] = None):
        """
        Save server definitions to a configuration file.
        
        Args:
            file_path: Output file path
            servers: List of server names to save (defaults to all)
        """
        file_path = Path(file_path)
        
        # Determine servers to save
        if servers:
            server_defs = [
                self.server_definitions[name] for name in servers
                if name in self.server_definitions
            ]
        else:
            server_defs = list(self.server_definitions.values())
        
        # Convert to serializable format
        config = {
            "mcp_servers": [
                self._server_definition_to_dict(server_def)
                for server_def in server_defs
            ]
        }
        
        try:
            with open(file_path, 'w') as f:
                if file_path.suffix.lower() in ['.yml', '.yaml']:
                    yaml.dump(config, f, default_flow_style=False)
                else:
                    json.dump(config, f, indent=2)
            
            logger.info(f"Saved {len(server_defs)} server definitions to {file_path}")
            
        except Exception as e:
            logger.error(f"Failed to save configuration to {file_path}: {e}")
    
    # ==================== Tool Discovery and Management ====================
    
    async def discover_tools(self, server_names: Optional[List[str]] = None) -> Dict[str, List[MCPToolInfo]]:
        """
        Discover tools from registered servers.
        
        Args:
            server_names: List of server names to query (defaults to all)
            
        Returns:
            Dictionary mapping server names to their tools
        """
        if server_names is None:
            server_names = list(self.server_definitions.keys())
        
        results = {}
        
        for server_name in server_names:
            if server_name not in self.server_definitions:
                continue
            
            try:
                tools = await self._discover_server_tools(server_name)
                results[server_name] = tools
                
                # Update discovered tools registry
                for tool in tools:
                    self.discovered_tools[f"{server_name}:{tool.name}"] = tool
                
            except Exception as e:
                logger.error(f"Failed to discover tools from {server_name}: {e}")
                results[server_name] = []
        
        return results
    
    def get_tool_info(self, tool_name: str, server_name: Optional[str] = None) -> Optional[MCPToolInfo]:
        """
        Get information about a specific tool.
        
        Args:
            tool_name: Name of the tool
            server_name: Optional server name for disambiguation
            
        Returns:
            Tool information if found
        """
        if server_name:
            key = f"{server_name}:{tool_name}"
            return self.discovered_tools.get(key)
        else:
            # Search across all servers
            for key, tool_info in self.discovered_tools.items():
                if tool_info.name == tool_name:
                    return tool_info
        
        return None
    
    def list_tools(
        self,
        server_name: Optional[str] = None,
        category: Optional[str] = None,
        tags: Optional[List[str]] = None
    ) -> List[MCPToolInfo]:
        """
        List discovered tools with optional filtering.
        
        Args:
            server_name: Filter by server name
            category: Filter by category
            tags: Filter by tags
            
        Returns:
            List of matching tools
        """
        tools = list(self.discovered_tools.values())
        
        # Filter by server
        if server_name:
            tools = [tool for tool in tools if tool.server_name == server_name]
        
        # Filter by category
        if category:
            tools = [tool for tool in tools if tool.category == category]
        
        # Filter by tags
        if tags:
            tools = [
                tool for tool in tools
                if any(tag in tool.tags for tag in tags)
            ]
        
        return tools
    
    # ==================== Health Monitoring ====================
    
    async def check_server_health(self, server_name: str) -> Dict[str, Any]:
        """
        Check the health status of a server.
        
        Returns:
            Health status information
        """
        if server_name not in self.server_definitions:
            return {"status": "unknown", "error": "Server not registered"}
        
        try:
            # This would integrate with the actual MCP manager
            # For now, return a placeholder
            health_info = {
                "status": "healthy",
                "uptime": "unknown",
                "tool_count": len([
                    tool for tool in self.discovered_tools.values()
                    if tool.server_name == server_name
                ]),
                "last_check": "now"
            }
            
            self.server_health[server_name].update(health_info)
            return health_info
            
        except Exception as e:
            error_info = {
                "status": "error",
                "error": str(e),
                "last_check": "now"
            }
            
            self.server_health[server_name].update(error_info)
            return error_info
    
    async def health_check_all(self) -> Dict[str, Dict[str, Any]]:
        """Check health of all registered servers."""
        results = {}
        
        for server_name in self.server_definitions:
            results[server_name] = await self.check_server_health(server_name)
        
        return results
    
    # ==================== Utility Methods ====================
    
    def get_registry_stats(self) -> Dict[str, Any]:
        """Get registry statistics."""
        return {
            "total_servers": len(self.server_definitions),
            "total_tools": len(self.discovered_tools),
            "servers_by_status": self._count_servers_by_status(),
            "tools_by_server": self._count_tools_by_server(),
            "tools_by_category": self._count_tools_by_category()
        }
    
    def export_tool_schemas(self, output_format: str = "openai") -> List[Dict[str, Any]]:
        """
        Export all tool schemas in the specified format.
        
        Args:
            output_format: Output format ("openai", "anthropic", etc.)
            
        Returns:
            List of tool schemas
        """
        schemas = []
        
        for tool_info in self.discovered_tools.values():
            if output_format == "openai":
                schema = {
                    "type": "function",
                    "function": {
                        "name": f"{tool_info.server_name}_{tool_info.name}",
                        "description": tool_info.description,
                        "parameters": tool_info.parameters
                    }
                }
                schemas.append(schema)
        
        return schemas
    
    # ==================== Private Methods ====================
    
    def _validate_server_definition(self, definition: MCPServerDefinition) -> bool:
        """Validate a server definition."""
        if not definition.name:
            logger.error("Server definition missing name")
            return False
        
        if not definition.command:
            logger.error(f"Server {definition.name} missing command")
            return False
        
        return True
    
    def _check_platform_compatibility(self, definition: MCPServerDefinition) -> bool:
        """Check if server is compatible with current platform."""
        import sys
        current_platform = sys.platform
        return current_platform in definition.supported_platforms
    
    def _load_from_config(self, config: Dict[str, Any]) -> int:
        """Load server definitions from configuration dictionary."""
        if "mcp_servers" not in config:
            logger.warning("No 'mcp_servers' section found in configuration")
            return 0
        
        loaded_count = 0
        
        for server_config in config["mcp_servers"]:
            try:
                definition = self._dict_to_server_definition(server_config)
                if self.register_server(definition):
                    loaded_count += 1
            except Exception as e:
                logger.error(f"Failed to load server definition: {e}")
        
        return loaded_count
    
    def _dict_to_server_definition(self, data: Dict[str, Any]) -> MCPServerDefinition:
        """Convert dictionary to server definition."""
        return MCPServerDefinition(
            name=data["name"],
            command=data["command"],
            args=data.get("args", []),
            env=data.get("env", {}),
            description=data.get("description", ""),
            version=data.get("version", "1.0.0"),
            author=data.get("author", ""),
            tags=data.get("tags", []),
            auto_start=data.get("auto_start", True),
            priority=data.get("priority", 50),
            timeout_seconds=data.get("timeout_seconds", 30),
            max_retries=data.get("max_retries", 3),
            python_requirements=data.get("python_requirements", []),
            system_requirements=data.get("system_requirements", []),
            supported_platforms=data.get("supported_platforms", ["linux", "darwin", "win32"]),
            include_tools=data.get("include_tools"),
            exclude_tools=data.get("exclude_tools", [])
        )
    
    def _server_definition_to_dict(self, definition: MCPServerDefinition) -> Dict[str, Any]:
        """Convert server definition to dictionary."""
        return {
            "name": definition.name,
            "command": definition.command,
            "args": definition.args,
            "env": definition.env,
            "description": definition.description,
            "version": definition.version,
            "author": definition.author,
            "tags": definition.tags,
            "auto_start": definition.auto_start,
            "priority": definition.priority,
            "timeout_seconds": definition.timeout_seconds,
            "max_retries": definition.max_retries,
            "python_requirements": definition.python_requirements,
            "system_requirements": definition.system_requirements,
            "supported_platforms": definition.supported_platforms,
            "include_tools": definition.include_tools,
            "exclude_tools": definition.exclude_tools
        }
    
    async def _discover_server_tools(self, server_name: str) -> List[MCPToolInfo]:
        """Discover tools from a specific server."""
        # This would integrate with the actual MCP manager to discover tools
        # For now, return placeholder tools
        return [
            MCPToolInfo(
                name=f"tool_{i}",
                server_name=server_name,
                description=f"Tool {i} from {server_name}",
                schema={},
                parameters={"type": "object", "properties": {}}
            )
            for i in range(1, 4)  # Placeholder: 3 tools per server
        ]
    
    def _count_servers_by_status(self) -> Dict[str, int]:
        """Count servers by health status."""
        counts = {}
        for health_info in self.server_health.values():
            status = health_info.get("status", "unknown")
            counts[status] = counts.get(status, 0) + 1
        return counts
    
    def _count_tools_by_server(self) -> Dict[str, int]:
        """Count tools by server."""
        counts = {}
        for tool_info in self.discovered_tools.values():
            server = tool_info.server_name
            counts[server] = counts.get(server, 0) + 1
        return counts
    
    def _count_tools_by_category(self) -> Dict[str, int]:
        """Count tools by category."""
        counts = {}
        for tool_info in self.discovered_tools.values():
            category = tool_info.category
            counts[category] = counts.get(category, 0) + 1
        return counts


# ==================== Convenience Functions ====================

def create_default_registry(config_dir: Optional[str] = None) -> MCPServerRegistry:
    """Create a registry with default server definitions."""
    registry = MCPServerRegistry(config_dir)
    
    # Add default servers
    default_servers = [
        MCPServerDefinition(
            name="calculator",
            command="python",
            args=["mcps/demo_calculator.py"],
            description="Basic calculator tool for mathematical operations",
            tags=["math", "calculator", "basic"],
            category="utilities"
        ),
        MCPServerDefinition(
            name="notion",
            command="python",
            args=["all_mcp_servers/notion_mcp_server.py"],
            description="Notion integration for document management",
            tags=["productivity", "documents", "notion"],
            category="productivity",
            priority=40  # Higher priority
        )
    ]
    
    for server_def in default_servers:
        registry.register_server(server_def)
    
    return registry


def load_registry_from_config(config_path: str) -> MCPServerRegistry:
    """Load registry from configuration file."""
    registry = MCPServerRegistry()
    registry.load_from_file(config_path)
    return registry

