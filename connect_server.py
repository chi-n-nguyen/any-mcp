#!/usr/bin/env python3
"""
MCP Server Connection CLI

This script allows you to automatically connect to a specific MCP server
and interact with it directly from the command line.

Usage:
    python connect_server.py --server <server_name>
    python connect_server.py --script <script_path>
    python connect_server.py --docker <docker_image>
    python connect_server.py --list
"""

import asyncio
import argparse
import sys
import os
from contextlib import AsyncExitStack
from typing import Optional, Dict, Any

from mcp_client import MCPClient
from mcp_manager import MCPManager
from core.claude import Claude
from core.cli_chat import CliChat
from core.cli import CliApp

from dotenv import load_dotenv

load_dotenv()

class ServerConnector:
    """Handles connection to specific MCP servers"""
    
    def __init__(self):
        self.client: Optional[MCPClient] = None
        self.manager = MCPManager()
        
    async def connect_to_configured_server(self, server_name: str) -> bool:
        """Connect to a server defined in mcp_config.yaml"""
        try:
            await self.manager.initialize()
            if server_name not in self.manager.active_clients:
                print(f"❌ Server '{server_name}' not found or failed to start")
                print("Available servers:")
                for name in self.manager.get_active_mcps():
                    print(f"  - {name}")
                return False
            
            self.client = self.manager.active_clients[server_name]
            print(f"✅ Connected to server: {server_name}")
            return True
                
        except Exception as e:
            print(f"❌ Failed to connect to {server_name}: {e}")
            return False
    
    async def connect_to_script(self, script_path: str) -> bool:
        """Connect to a local Python script MCP server"""
        try:
            if not os.path.exists(script_path):
                print(f"❌ Script not found: {script_path}")
                return False
            
            # Determine if we should use uv or python
            use_uv = os.getenv("USE_UV", "0") == "1"
            
            if use_uv:
                command, args = "uv", ["run", script_path]
            else:
                command, args = "python", [script_path]
            
            self.client = MCPClient(command=command, args=args)
            await self.client.connect()
            print(f"✅ Connected to script: {script_path}")
            return True
            
        except Exception as e:
            print(f"❌ Failed to connect to script {script_path}: {e}")
            return False
    
    async def connect_to_docker(self, docker_image: str, env_vars: Optional[Dict[str, str]] = None) -> bool:
        """Connect to a Docker-based MCP server"""
        try:
            env = os.environ.copy()
            if env_vars:
                env.update(env_vars)
            
            docker_args = ["run", "-i", "--rm"]
            
            # Add environment variables
            if env_vars:
                for key, value in env_vars.items():
                    docker_args.extend(["-e", f"{key}={value}"])
            
            docker_args.append(docker_image)
            
            self.client = MCPClient(
                command="docker", 
                args=docker_args,
                env=env
            )
            await self.client.connect()
            print(f"✅ Connected to Docker image: {docker_image}")
            return True
            
        except Exception as e:
            print(f"❌ Failed to connect to Docker image {docker_image}: {e}")
            return False
    
    async def list_available_servers(self):
        """List all available configured servers"""
        try:
            async with self.manager:
                status = await self.manager.get_mcp_status()
                
                print("\n📋 Available MCP Servers:")
                print("-" * 50)
                
                for name, info in status.items():
                    emoji = "✅" if info.get("active") and info.get("healthy") else "❌"
                    enabled = "✓" if info.get("enabled") else "✗"
                    print(f"{emoji} {name:<15} [{info.get('type', 'unknown'):<6}] (enabled: {enabled})")
                    if info.get("description"):
                        print(f"    {info['description']}")
                    print()
                
        except Exception as e:
            print(f"❌ Failed to list servers: {e}")
    
    async def show_server_info(self):
        """Show information about the connected server"""
        if not self.client:
            print("❌ No server connected")
            return
        
        try:
            # List available tools
            tools = await self.client.list_tools()
            print(f"\n🔧 Available Tools ({len(tools)}):")
            print("-" * 30)
            for tool in tools:
                print(f"  • {tool.name}")
                if tool.description:
                    print(f"    {tool.description}")
                print()
            
            # List available prompts
            prompts = await self.client.list_prompts()
            if prompts:
                print(f"\n💭 Available Prompts ({len(prompts)}):")
                print("-" * 30)
                for prompt in prompts:
                    print(f"  • {prompt.name}")
                    if prompt.description:
                        print(f"    {prompt.description}")
                    print()
                    
        except Exception as e:
            print(f"❌ Failed to get server info: {e}")
    
    async def start_interactive_session(self):
        """Start an interactive chat session with the connected server"""
        if not self.client:
            print("❌ No server connected")
            return
        
        try:
            # Check if Claude is configured for enhanced chat
            claude_model = os.getenv("CLAUDE_MODEL", "")
            anthropic_api_key = os.getenv("ANTHROPIC_API_KEY", "")
            
            if claude_model and anthropic_api_key:
                print("🤖 Starting enhanced chat with Claude integration...")
                try:
                    claude_service = Claude(model=claude_model)
                    clients = {"target_server": self.client}
                    
                    chat = CliChat(
                        doc_client=self.client,
                        clients=clients,
                        claude_service=claude_service,
                    )
                    
                    cli = CliApp(chat)
                    await cli.initialize()
                    
                    print("\n🚀 Interactive session ready!")
                    print("💡 You can use tools directly or ask Claude to help you.")
                    print("   Type your questions or commands, and press Ctrl+C to exit.\n")
                    
                    await cli.run()
                except Exception as e:
                    print(f"❌ Claude integration failed: {e}")
                    print("🔧 Falling back to direct tool interaction mode...")
                    await self._basic_interaction_loop()
            else:
                print("🔧 Starting direct tool interaction mode...")
                print("💡 Claude not configured. You can call tools directly.")
                print("   Available commands:")
                print("   - 'tools' - list available tools")
                print("   - 'prompts' - list available prompts")
                print("   - 'call <tool_name> <args>' - call a tool")
                print("   - 'quit' - exit")
                print()
                
                await self._basic_interaction_loop()
                
        except KeyboardInterrupt:
            print("\n👋 Session ended.")
        except Exception as e:
            print(f"❌ Session error: {e}")
    
    async def _basic_interaction_loop(self):
        """Basic interaction loop without Claude integration"""
        while True:
            try:
                user_input = input("> ").strip()
                
                if user_input.lower() in ['quit', 'exit']:
                    break
                elif user_input.lower() == 'tools':
                    tools = await self.client.list_tools()
                    print(f"Available tools: {[tool.name for tool in tools]}")
                elif user_input.lower() == 'prompts':
                    prompts = await self.client.list_prompts()
                    print(f"Available prompts: {[prompt.name for prompt in prompts]}")
                elif user_input.startswith('call '):
                    parts = user_input[5:].split(' ', 1)
                    tool_name = parts[0]
                    args = {}
                    if len(parts) > 1:
                        # Simple argument parsing (key=value format)
                        try:
                            for arg in parts[1].split(','):
                                if '=' in arg:
                                    key, value = arg.strip().split('=', 1)
                                    args[key.strip()] = value.strip()
                        except:
                            print("❌ Invalid argument format. Use: key=value,key2=value2")
                            continue
                    
                    result = await self.client.call_tool(tool_name, args)
                    if result:
                        print(f"Result: {result}")
                    else:
                        print("❌ Tool call failed")
                else:
                    print("❌ Unknown command. Try 'tools', 'prompts', 'call <tool>', or 'quit'")
                    
            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"❌ Error: {e}")


async def main():
    parser = argparse.ArgumentParser(
        description="Connect to a specific MCP server and interact with it",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        "--server", "-s",
        help="Name of the configured server to connect to"
    )
    
    parser.add_argument(
        "--script", 
        help="Path to a local Python MCP script"
    )
    
    parser.add_argument(
        "--docker", "-d",
        help="Docker image name for MCP server"
    )
    
    parser.add_argument(
        "--env", "-e",
        action="append",
        help="Environment variables for Docker (format: KEY=VALUE)"
    )
    
    parser.add_argument(
        "--list", "-l",
        action="store_true",
        help="List all available configured servers"
    )
    
    parser.add_argument(
        "--info", "-i",
        action="store_true",
        help="Show server information after connecting"
    )
    
    parser.add_argument(
        "--no-chat",
        action="store_true", 
        help="Don't start interactive session, just connect and show info"
    )
    
    args = parser.parse_args()
    
    connector = ServerConnector()
    
    # Handle list command
    if args.list:
        await connector.list_available_servers()
        return
    
    # Validate arguments
    connection_methods = sum([bool(args.server), bool(args.script), bool(args.docker)])
    if connection_methods == 0:
        print("❌ You must specify one connection method:")
        print("   --server <name>     Connect to configured server")
        print("   --script <path>     Connect to local script")
        print("   --docker <image>    Connect to Docker image")
        print("   --list              List available servers")
        return
    
    if connection_methods > 1:
        print("❌ Please specify only one connection method")
        return
    
    # Connect to the specified server
    connected = False
    
    async with AsyncExitStack() as stack:
        if args.server:
            # For configured servers, we need to manage the manager lifecycle
            await stack.enter_async_context(connector.manager)
            connected = await connector.connect_to_configured_server(args.server)
        elif args.script:
            connected = await connector.connect_to_script(args.script)
            if connected and connector.client:
                await stack.enter_async_context(connector.client)
        elif args.docker:
            env_vars = {}
            if args.env:
                for env_pair in args.env:
                    if '=' in env_pair:
                        key, value = env_pair.split('=', 1)
                        env_vars[key] = value
            
            connected = await connector.connect_to_docker(args.docker, env_vars)
            if connected and connector.client:
                await stack.enter_async_context(connector.client)
        
        if not connected:
            print("❌ Failed to connect to server")
            return
        
        # Show server info if requested or if in no-chat mode
        if args.info or args.no_chat:
            await connector.show_server_info()
        
        # Start interactive session unless disabled
        if not args.no_chat:
            await connector.start_interactive_session()


if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")