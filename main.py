import asyncio
import sys
import os
from dotenv import load_dotenv
from contextlib import AsyncExitStack

from mcp_client import MCPClient
from mcp_manager import MCPManager
from core.claude import Claude

from core.cli_chat import CliChat
from core.cli import CliApp

load_dotenv()

# Anthropic Config
claude_model = os.getenv("CLAUDE_MODEL", "")
anthropic_api_key = os.getenv("ANTHROPIC_API_KEY", "")


assert claude_model, "Error: CLAUDE_MODEL cannot be empty. Update .env"
assert anthropic_api_key, (
    "Error: ANTHROPIC_API_KEY cannot be empty. Update .env"
)


async def main():
    claude_service = Claude(model=claude_model)

    # Initialize MCP Manager to handle all configured MCPs
    mcp_manager = MCPManager()
    
    async with AsyncExitStack() as stack:
        # Setup MCP Manager with configured MCPs
        await stack.enter_async_context(mcp_manager)
        
        # Get clients from MCP manager + any additional command line MCPs
        clients = {}
        
        # Add MCPs from manager
        for mcp_name, client in mcp_manager.active_clients.items():
            clients[mcp_name] = client
        
        # Add default document client if no MCPs loaded or for backward compatibility
        server_scripts = sys.argv[1:]
        if not clients or server_scripts:
            command, args = (
                ("uv", ["run", "mcp_server.py"])
                if os.getenv("USE_UV", "0") == "1"
                else ("python3", ["mcp_server.py"])
            )
            doc_client = await stack.enter_async_context(
                MCPClient(command=command, args=args)
            )
            clients["doc_client"] = doc_client

        # Add any additional server scripts from command line
        for i, server_script in enumerate(server_scripts):
            client_id = f"client_{i}_{server_script}"
            client = await stack.enter_async_context(
                MCPClient(command="uv", args=["run", server_script])
            )
            clients[client_id] = client

        # Create chat with all clients
        doc_client = clients.get("doc_client") or list(clients.values())[0]
        chat = CliChat(
            doc_client=doc_client,
            clients=clients,
            claude_service=claude_service,
        )

        cli = CliApp(chat)
        await cli.initialize()
        
        # Show status of loaded MCPs
        print(f"\n🚀 any-mcp CLI Ready with {len(clients)} MCP client(s)!")
        if hasattr(mcp_manager, 'get_mcp_status'):
            try:
                status = await mcp_manager.get_mcp_status()
                print("📋 MCP Status:")
                for name, info in status.items():
                    emoji = "✅" if info.get("active") and info.get("healthy") else "❌"
                    print(f"   {emoji} {name}: {info.get('description', 'No description')}")
            except Exception as e:
                print(f"   ⚠️  Could not get MCP status: {e}")
        
        await cli.run()


if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    asyncio.run(main())
