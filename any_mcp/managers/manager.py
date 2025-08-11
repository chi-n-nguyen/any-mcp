import asyncio
import logging
import os
from typing import Dict, List, Optional, Any
from contextlib import AsyncExitStack

from any_mcp.core.client import MCPClient
from any_mcp.managers.installer import MCPInstaller, MCPConfig, MCPType
from mcp import types

logger = logging.getLogger(__name__)


class MCPManager:
    """
    MCP lifecycle manager for starting, stopping, and monitoring MCP servers.
    Provides health checks, tool orchestration, and status reporting.
    """
    def __init__(self, config_path: str = "config/mcp_config.yaml"):
        self.installer = MCPInstaller(config_path)
        self.active_clients: Dict[str, MCPClient] = {}
        self.exit_stack = AsyncExitStack()
        self._initialized = False

    async def initialize(self):
        """Initialize the MCP manager and start enabled MCPs."""
        if self._initialized:
            return

        try:
            enabled_mcps = self.installer.get_enabled_mcps()
            logger.info(f"Initializing {len(enabled_mcps)} enabled MCPs")

            # Start all enabled MCPs
            for mcp_config in enabled_mcps:
                await self.setup_mcp(mcp_config.name)

            self._initialized = True
            logger.info("MCP manager initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize MCP manager: {e}")
            raise

    async def setup_mcp(self, mcp_name: str) -> bool:
        """
        Setup and start an MCP server.
        
        Args:
            mcp_name: Name of the MCP to setup
            
        Returns:
            bool: True if setup successful
        """
        if mcp_name in self.active_clients:
            logger.info(f"MCP {mcp_name} is already active")
            return True

        mcp_config = self.installer.get_mcp_config(mcp_name)
        if not mcp_config:
            logger.error(f"MCP {mcp_name} not found in installed MCPs")
            return False

        if not mcp_config.enabled:
            logger.warning(f"MCP {mcp_name} is disabled")
            return False

        try:
            # Create MCP client based on type
            if mcp_config.type == MCPType.DOCKER:
                client = await self._setup_docker_mcp(mcp_config)
            elif mcp_config.type == MCPType.LOCAL:
                client = await self._setup_local_mcp(mcp_config)
            else:
                logger.error(f"Unsupported MCP type: {mcp_config.type}")
                return False

            if client:
                # Register with exit stack for cleanup
                await self.exit_stack.enter_async_context(client)
                self.active_clients[mcp_name] = client
                logger.info(f"Successfully setup MCP: {mcp_name}")
                return True
            else:
                logger.error(f"Failed to create client for MCP: {mcp_name}")
                return False

        except Exception as e:
            logger.error(f"Error setting up MCP {mcp_name}: {e}")
            return False

    async def _setup_docker_mcp(self, mcp_config: MCPConfig) -> Optional[MCPClient]:
        """Setup a Docker-based MCP."""
        try:
            # Prepare environment variables
            env = os.environ.copy()
            env.update(mcp_config.env_vars)

            # Create client with docker command
            client = MCPClient(
                command="docker",
                args=[
                    "run", "-i", "--rm",
                    *[item for key, value in mcp_config.env_vars.items() 
                      for item in ["-e", f"{key}={value}"]],
                    mcp_config.source
                ],
                env=env
            )

            # Test connection
            await client.connect()
            return client

        except Exception as e:
            logger.error(f"Failed to setup Docker MCP {mcp_config.name}: {e}")
            return None

    async def _setup_local_mcp(self, mcp_config: MCPConfig) -> Optional[MCPClient]:
        """Setup a local MCP (Python scripts, NPX packages, or other commands)."""
        try:
            # Prepare environment variables
            env = os.environ.copy()
            env.update(mcp_config.env_vars)

            # Parse the source command
            source_parts = mcp_config.source.split()
            
            if source_parts[0] == "npx":
                # Handle NPX commands
                client = MCPClient(
                    command="npx",
                    args=source_parts[1:],  # Everything after "npx"
                    env=env
                )
            elif mcp_config.source.endswith(".py"):
                # Handle Python scripts
                use_uv = os.getenv("USE_UV", "0") == "1"
                if use_uv:
                    client = MCPClient(
                        command="uv",
                        args=["run", mcp_config.source],
                        env=env
                    )
                else:
                    client = MCPClient(
                        command="python",
                        args=[mcp_config.source],
                        env=env
                    )
            else:
                # Handle other commands (parse the full command)
                client = MCPClient(
                    command=source_parts[0],
                    args=source_parts[1:] if len(source_parts) > 1 else [],
                    env=env
                )

            # Test connection
            await client.connect()
            return client

        except Exception as e:
            logger.error(f"Failed to setup local MCP {mcp_config.name}: {e}")
            return None

    async def call_mcp(self, mcp_name: str, tool_name: str, args: Dict[str, Any]) -> Optional[types.CallToolResult]:
        """
        Call a tool on a specific MCP.
        
        Args:
            mcp_name: Name of the MCP
            tool_name: Name of the tool to call
            args: Arguments for the tool
            
        Returns:
            CallToolResult or None if failed
        """
        if mcp_name not in self.active_clients:
            logger.error(f"MCP {mcp_name} is not active")
            return None

        try:
            client = self.active_clients[mcp_name]
            result = await client.call_tool(tool_name, args)
            logger.info(f"Successfully called {tool_name} on {mcp_name}")
            return result
        except Exception as e:
            logger.error(f"Failed to call tool {tool_name} on {mcp_name}: {e}")
            return None

    async def list_mcp_tools(self, mcp_name: str) -> List[types.Tool]:
        """
        List available tools for a specific MCP.
        
        Args:
            mcp_name: Name of the MCP
            
        Returns:
            List of available tools
        """
        if mcp_name not in self.active_clients:
            logger.error(f"MCP {mcp_name} is not active")
            return []

        try:
            client = self.active_clients[mcp_name]
            tools = await client.list_tools()
            return tools
        except Exception as e:
            logger.error(f"Failed to list tools for {mcp_name}: {e}")
            return []

    async def list_all_tools(self) -> Dict[str, List[types.Tool]]:
        """
        List all available tools from all active MCPs.
        
        Returns:
            Dictionary mapping MCP names to their tools
        """
        all_tools = {}
        for mcp_name in self.active_clients:
            tools = await self.list_mcp_tools(mcp_name)
            all_tools[mcp_name] = tools
        return all_tools

    def get_active_mcps(self) -> List[str]:
        """Get list of currently active MCP names."""
        return list(self.active_clients.keys())

    def get_installed_mcps(self) -> List[MCPConfig]:
        """Get list of all installed MCPs."""
        return self.installer.list_installed_mcps()

    async def stop_mcp(self, mcp_name: str) -> bool:
        """
        Stop a specific MCP.
        
        Args:
            mcp_name: Name of the MCP to stop
            
        Returns:
            bool: True if stopped successfully
        """
        if mcp_name not in self.active_clients:
            logger.warning(f"MCP {mcp_name} is not active")
            return False

        try:
            client = self.active_clients[mcp_name]
            await client.cleanup()
            del self.active_clients[mcp_name]
            logger.info(f"Successfully stopped MCP: {mcp_name}")
            return True
        except Exception as e:
            logger.error(f"Failed to stop MCP {mcp_name}: {e}")
            return False

    async def restart_mcp(self, mcp_name: str) -> bool:
        """
        Restart a specific MCP.
        
        Args:
            mcp_name: Name of the MCP to restart
            
        Returns:
            bool: True if restarted successfully
        """
        await self.stop_mcp(mcp_name)
        return await self.setup_mcp(mcp_name)

    async def health_check(self, mcp_name: str) -> bool:
        """
        Check if an MCP is healthy and responsive.
        
        Args:
            mcp_name: Name of the MCP to check
            
        Returns:
            bool: True if healthy
        """
        if mcp_name not in self.active_clients:
            return False

        try:
            client = self.active_clients[mcp_name]
            # Try to list tools as a health check
            tools = await client.list_tools()
            return True
        except Exception as e:
            logger.warning(f"Health check failed for {mcp_name}: {e}")
            return False

    async def get_mcp_status(self) -> Dict[str, Dict[str, Any]]:
        """
        Get status information for all MCPs.
        
        Returns:
            Dictionary with MCP status information
        """
        status = {}
        
        # Get installed MCPs
        for mcp_config in self.installer.list_installed_mcps():
            is_active = mcp_config.name in self.active_clients
            is_healthy = await self.health_check(mcp_config.name) if is_active else False
            
            status[mcp_config.name] = {
                "type": mcp_config.type.value,
                "enabled": mcp_config.enabled,
                "active": is_active,
                "healthy": is_healthy,
                "description": mcp_config.description
            }
        
        return status

    def register_with_llm(self, mcp_name: str, llm_instance=None):
        """
        Register MCP tools with an LLM instance.
        
        Args:
            mcp_name: Name of the MCP
            llm_instance: LLM instance to register tools with (placeholder for future implementation)
        """
        # Placeholder for LLM integration
        # In the future, this would register tools with specific LLM frameworks
        logger.info(f"LLM registration for {mcp_name} - placeholder implementation")

    async def cleanup(self):
        """Clean up all active MCP clients."""
        try:
            await self.exit_stack.aclose()
            self.active_clients.clear()
            self._initialized = False
            logger.info("MCP manager cleaned up successfully")
        except Exception as e:
            logger.error(f"Error during MCP manager cleanup: {e}")

    async def __aenter__(self):
        await self.initialize()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.cleanup() 