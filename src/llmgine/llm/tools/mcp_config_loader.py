"""
MCP Configuration Loader

Loads and manages MCP server configurations from YAML files.
Supports environment variable substitution and validation.
"""

import os
import logging
from typing import Dict, Any, List, Optional
import yaml

logger = logging.getLogger(__name__)


class MCPServerConfig:
    """Configuration for a single MCP server."""
    
    def __init__(self, name: str, config: Dict[str, Any]):
        self.name = name
        self.type = config.get("type", "local")
        self.command = config.get("command", "")
        self.args = config.get("args", [])
        self.enabled = config.get("enabled", False)
        self.env_vars = config.get("env_vars", {})
        self.description = config.get("description", "")
        self.install_cmd = config.get("install_cmd", "")
        
        # Resolve environment variables in env_vars
        self.resolved_env = self._resolve_env_vars()
    
    def _resolve_env_vars(self) -> Dict[str, str]:
        """Resolve environment variable references in env_vars."""
        resolved = {}
        
        for key, value in self.env_vars.items():
            if isinstance(value, str) and value.startswith("${") and value.endswith("}"):
                env_var_name = value[2:-1]  # Remove ${ and }
                env_value = os.getenv(env_var_name)
                
                if env_value:
                    resolved[key] = env_value
                else:
                    logger.warning(f"Environment variable {env_var_name} not set for server {self.name}")
            else:
                resolved[key] = str(value)
        
        return resolved
    
    def is_available(self) -> bool:
        """Check if this server can be started (all required env vars set)."""
        if not self.enabled:
            return False
        
        # Check if all required environment variables are available
        for key, value in self.env_vars.items():
            if isinstance(value, str) and value.startswith("${") and value.endswith("}"):
                env_var_name = value[2:-1]
                if not os.getenv(env_var_name):
                    return False
        
        return True
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "name": self.name,
            "type": self.type,
            "command": self.command,
            "args": self.args,
            "enabled": self.enabled,
            "env_vars": self.env_vars,
            "resolved_env": self.resolved_env,
            "description": self.description,
            "install_cmd": self.install_cmd,
            "available": self.is_available()
        }


class MCPConfigLoader:
    """Loads and manages MCP server configurations."""
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize config loader.
        
        Args:
            config_path: Path to YAML config file. If None, uses default locations.
        """
        self.config_path = config_path or self._find_config_file()
        self.servers: Dict[str, MCPServerConfig] = {}
        self.defaults: Dict[str, Any] = {}
        
        if self.config_path and os.path.exists(self.config_path):
            self.load_config()
        else:
            logger.warning(f"MCP config file not found at {self.config_path}")
    
    def _find_config_file(self) -> str:
        """Find the MCP configuration file in standard locations."""
        possible_paths = [
            "config/mcp_servers_config.yaml",
            "../config/mcp_servers_config.yaml",
            "../../config/mcp_servers_config.yaml",
            "../../../config/mcp_servers_config.yaml",
            "../../../../config/mcp_servers_config.yaml",
            os.path.expanduser("~/.llmgine/mcp_servers_config.yaml"),
            "/etc/llmgine/mcp_servers_config.yaml"
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                return path
        
        return "config/mcp_servers_config.yaml"  # Default
    
    def load_config(self):
        """Load configuration from YAML file."""
        try:
            with open(self.config_path, 'r') as f:
                config = yaml.safe_load(f)
            
            # Load defaults
            self.defaults = config.get("defaults", {})
            
            # Load server configurations
            mcp_servers = config.get("mcp_servers", {})
            
            for name, server_config in mcp_servers.items():
                self.servers[name] = MCPServerConfig(name, server_config)
            
            logger.info(f"Loaded {len(self.servers)} MCP server configurations from {self.config_path}")
            
        except Exception as e:
            logger.error(f"Failed to load MCP config from {self.config_path}: {e}")
    
    def get_enabled_servers(self) -> List[MCPServerConfig]:
        """Get list of enabled MCP servers."""
        return [server for server in self.servers.values() if server.enabled]
    
    def get_available_servers(self) -> List[MCPServerConfig]:
        """Get list of servers that are enabled and have required env vars set."""
        return [server for server in self.servers.values() if server.is_available()]
    
    def get_server(self, name: str) -> Optional[MCPServerConfig]:
        """Get a specific server configuration by name."""
        return self.servers.get(name)
    
    def list_servers(self) -> Dict[str, Dict[str, Any]]:
        """List all servers with their configuration details."""
        return {name: server.to_dict() for name, server in self.servers.items()}
    
    def get_missing_env_vars(self) -> Dict[str, List[str]]:
        """Get list of missing environment variables for each server."""
        missing = {}
        
        for name, server in self.servers.items():
            if server.enabled:
                missing_vars = []
                for key, value in server.env_vars.items():
                    if isinstance(value, str) and value.startswith("${") and value.endswith("}"):
                        env_var_name = value[2:-1]
                        if not os.getenv(env_var_name):
                            missing_vars.append(env_var_name)
                
                if missing_vars:
                    missing[name] = missing_vars
        
        return missing
    
    def get_install_commands(self) -> Dict[str, str]:
        """Get installation commands for servers that have them."""
        return {
            name: server.install_cmd 
            for name, server in self.servers.items() 
            if server.install_cmd
        }


# Global config loader instance
_config_loader: Optional[MCPConfigLoader] = None


def get_config_loader() -> MCPConfigLoader:
    """Get the global MCP configuration loader."""
    global _config_loader
    if _config_loader is None:
        _config_loader = MCPConfigLoader()
    return _config_loader


def load_mcp_config(config_path: Optional[str] = None) -> MCPConfigLoader:
    """Load MCP configuration from file."""
    return MCPConfigLoader(config_path)