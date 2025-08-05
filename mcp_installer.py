import os
import json
import yaml
import shutil
import asyncio
import logging
from pathlib import Path
from typing import Dict, List, Optional, Union
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class MCPType(Enum):
    DOCKER = "docker"
    LOCAL = "local"
    REGISTRY = "registry"


@dataclass
class MCPConfig:
    name: str
    type: MCPType
    source: str
    env_vars: Dict[str, str] = None
    enabled: bool = True
    description: str = ""
    
    def __post_init__(self):
        if self.env_vars is None:
            self.env_vars = {}


class MCPInstaller:
    def __init__(self, config_path: str = "mcp_config.yaml"):
        self.config_path = Path(config_path)
        self.mcps_dir = Path("mcps")
        self.mcps_dir.mkdir(exist_ok=True)
        self.installed_mcps: Dict[str, MCPConfig] = {}
        self._load_config()

    def _load_config(self):
        """Load MCP configuration from file."""
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r') as f:
                    config_data = yaml.safe_load(f) or {}
                
                for name, mcp_data in config_data.get('installed_mcps', {}).items():
                    self.installed_mcps[name] = MCPConfig(
                        name=name,
                        type=MCPType(mcp_data['type']),
                        source=mcp_data['source'],
                        env_vars=mcp_data.get('env_vars', {}),
                        enabled=mcp_data.get('enabled', True),
                        description=mcp_data.get('description', '')
                    )
                logger.info(f"Loaded {len(self.installed_mcps)} MCPs from config")
            except Exception as e:
                logger.error(f"Failed to load config: {e}")
                self.installed_mcps = {}
        else:
            logger.info("No existing config found, starting fresh")

    def _save_config(self):
        """Save current MCP configuration to file."""
        config_data = {
            'installed_mcps': {
                name: {
                    'type': mcp.type.value,
                    'source': mcp.source,
                    'env_vars': mcp.env_vars,
                    'enabled': mcp.enabled,
                    'description': mcp.description
                }
                for name, mcp in self.installed_mcps.items()
            }
        }
        
        try:
            with open(self.config_path, 'w') as f:
                yaml.dump(config_data, f, default_flow_style=False)
            logger.info(f"Saved config to {self.config_path}")
        except Exception as e:
            logger.error(f"Failed to save config: {e}")
            raise

    def install_mcp(self, name: str, source: str, description: str = "", env_vars: Dict[str, str] = None) -> bool:
        """
        Install an MCP from various sources.
        
        Args:
            name: Unique name for the MCP
            source: Source URL/path (docker://image, local://path, registry://name)
            description: Optional description
            env_vars: Environment variables required by the MCP
            
        Returns:
            bool: True if installation successful
        """
        if env_vars is None:
            env_vars = {}
            
        try:
            # Parse source type
            if source.startswith("docker://"):
                mcp_type = MCPType.DOCKER
                source_path = source.replace("docker://", "")
            elif source.startswith("local://"):
                mcp_type = MCPType.LOCAL
                source_path = source.replace("local://", "")
                # Validate local file exists
                if not Path(source_path).exists():
                    raise FileNotFoundError(f"Local MCP file not found: {source_path}")
            elif source.startswith("registry://"):
                mcp_type = MCPType.REGISTRY
                source_path = source.replace("registry://", "")
                # TODO: Implement registry lookup
                raise NotImplementedError("Registry sources not yet implemented")
            else:
                raise ValueError(f"Invalid source format: {source}")

            # Create MCP config
            mcp_config = MCPConfig(
                name=name,
                type=mcp_type,
                source=source_path,
                env_vars=env_vars,
                description=description
            )

            # Install based on type
            if mcp_type == MCPType.DOCKER:
                success = self._install_docker_mcp(mcp_config)
            elif mcp_type == MCPType.LOCAL:
                success = self._install_local_mcp(mcp_config)
            else:
                success = False

            if success:
                self.installed_mcps[name] = mcp_config
                self._save_config()
                logger.info(f"Successfully installed MCP: {name}")
                return True
            else:
                logger.error(f"Failed to install MCP: {name}")
                return False

        except Exception as e:
            logger.error(f"Error installing MCP {name}: {e}")
            return False

    def _install_docker_mcp(self, mcp: MCPConfig) -> bool:
        """Install a Docker-based MCP."""
        try:
            # Check if Docker is available
            result = os.system("docker --version > /dev/null 2>&1")
            if result != 0:
                raise RuntimeError("Docker is not available")

            # Try to pull the image to validate it exists
            pull_result = os.system(f"docker pull {mcp.source} > /dev/null 2>&1")
            if pull_result != 0:
                logger.warning(f"Could not pull image {mcp.source}, will try to run anyway")

            logger.info(f"Docker MCP {mcp.name} ready for use")
            return True
        except Exception as e:
            logger.error(f"Failed to install Docker MCP: {e}")
            return False

    def _install_local_mcp(self, mcp: MCPConfig) -> bool:
        """Install a local MCP."""
        try:
            source_path = Path(mcp.source)
            target_path = self.mcps_dir / f"{mcp.name}.py"
            
            # Copy local file to mcps directory
            if source_path != target_path:
                shutil.copy2(source_path, target_path)
                # Update source to point to copied file
                mcp.source = str(target_path)
            
            logger.info(f"Local MCP {mcp.name} installed to {target_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to install local MCP: {e}")
            return False

    def uninstall_mcp(self, name: str) -> bool:
        """Remove an installed MCP."""
        if name not in self.installed_mcps:
            logger.warning(f"MCP {name} is not installed")
            return False

        try:
            mcp = self.installed_mcps[name]
            
            # Clean up based on type
            if mcp.type == MCPType.LOCAL:
                # Remove copied file if it's in our mcps directory
                target_path = self.mcps_dir / f"{name}.py"
                if target_path.exists():
                    target_path.unlink()
            
            # Remove from config
            del self.installed_mcps[name]
            self._save_config()
            
            logger.info(f"Successfully uninstalled MCP: {name}")
            return True
        except Exception as e:
            logger.error(f"Failed to uninstall MCP {name}: {e}")
            return False

    def list_installed_mcps(self) -> List[MCPConfig]:
        """Return list of installed MCPs."""
        return list(self.installed_mcps.values())

    def get_mcp_config(self, name: str) -> Optional[MCPConfig]:
        """Get configuration for a specific MCP."""
        return self.installed_mcps.get(name)

    def enable_mcp(self, name: str) -> bool:
        """Enable an MCP."""
        if name in self.installed_mcps:
            self.installed_mcps[name].enabled = True
            self._save_config()
            return True
        return False

    def disable_mcp(self, name: str) -> bool:
        """Disable an MCP."""
        if name in self.installed_mcps:
            self.installed_mcps[name].enabled = False
            self._save_config()
            return True
        return False

    def get_enabled_mcps(self) -> List[MCPConfig]:
        """Return list of enabled MCPs."""
        return [mcp for mcp in self.installed_mcps.values() if mcp.enabled] 