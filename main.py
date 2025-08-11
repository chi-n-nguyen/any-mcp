import asyncio
import sys
import os
from dotenv import load_dotenv
from contextlib import AsyncExitStack

from mcp_client import MCPClient
from mcp_manager import MCPManager
from core.claude import Claude
from core.gemini import Gemini

from core.cli_chat import CliChat
from core.cli import CliApp

load_dotenv()

# LLM Config - Support both Claude and Gemini
llm_provider = os.getenv("LLM_PROVIDER", "gemini").lower()

# Claude Config
claude_model = os.getenv("CLAUDE_MODEL", "")
anthropic_api_key = os.getenv("ANTHROPIC_API_KEY", "")

# Gemini Config  
gemini_model = os.getenv("GEMINI_MODEL", "gemini-1.5-pro")
gemini_api_key = os.getenv("GEMINI_API_KEY", "")

# Validate configuration based on provider
if llm_provider == "claude":
    assert claude_model, "Error: CLAUDE_MODEL cannot be empty when using Claude. Update .env"
    assert anthropic_api_key, "Error: ANTHROPIC_API_KEY cannot be empty when using Claude. Update .env"
elif llm_provider == "gemini":
    assert gemini_api_key, "Error: GEMINI_API_KEY cannot be empty when using Gemini. Update .env"
else:
    raise ValueError(f"Unsupported LLM_PROVIDER: {llm_provider}. Use 'claude' or 'gemini'")


async def main():
    # Initialize LLM service based on provider
    if llm_provider == "claude":
        llm_service = Claude(model=claude_model)
    elif llm_provider == "gemini":
        llm_service = Gemini(model=gemini_model, api_key=gemini_api_key)
    else:
        raise ValueError(f"Unsupported LLM provider: {llm_provider}")

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
            claude_service=llm_service,
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
