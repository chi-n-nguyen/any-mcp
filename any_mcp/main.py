import asyncio
import sys
import os
from dotenv import load_dotenv
from contextlib import AsyncExitStack

# for mcp functionality
from any_mcp.core.client import MCPClient
from any_mcp.managers.manager import MCPManager
from any_mcp.core.claude import Claude
from any_mcp.core.gemini import Gemini

# for better CLI visualization
from any_mcp.core.cli_chat import CliChat
from any_mcp.core.cli import CliApp

# for loading constants + API key
import config

# LLM Config - Support both Claude and Gemini, load the constant for Claude + Gemini Provider
llm_provider = config.LLM_PROVIDER
claude_provider = config.CLAUDE_LLM_PROVIDER
gemini_provider = config.GEMINI_LLM_PROVIDER

# Claude Config
claude_model = config.CLAUDE_MODEL
anthropic_api_key = config.ANTHROPIC_API_KEY

# Gemini Config  
gemini_model = config.GEMINI_MODEL
gemini_api_key = config.GEMINI_API_KEY

'''                                                                                      
 Workflow / Execution Order of this Script:                                           
                                                                                      
 1. Import all necessary modules and classes, including:                              
    - Standard libraries (asyncio, sys, os, dotenv, contextlib)                       
    - Core MCP classes (MCPClient, MCPManager, Claude, Gemini)                        
    - CLI utilities (CliChat, CliApp)                                                 
    - Configuration loader (config.py)                                               
                                                                                      
 2. Load configuration constants from config.py:                                       
    - LLM provider selection (llm_provider, claude_provider, gemini_provider)         
    - Model names and API keys for Claude and Gemini                                  
                                                                                      
 3. Define check_llm_provider_config():                                               
    - This function checks that the required config values (model, API key)           
      are present for the selected LLM provider.                                      
    - Uses a hashmap (provider_checks) to map provider to required values.            
    - Raises assertion error or ValueError if config is missing or provider is wrong.
                                                                                      
 4. Immediately call check_llm_provider_config() to validate config at startup.        
                                                                                      
 5. Define initialize_llm_service_based_on_llm_provider(llm_provider):                
    - Uses a hashmap (llm_service_map) to map provider to the correct LLM service     
      class instance (Claude or Gemini).                                              
    - Returns the initialized LLM service object.                                     
                                                                                      
 6. Define the main() async function:                                                 
    - Initializes the LLM service using initialize_llm_service_based_on_llm_provider. 
    - Creates an MCPManager instance to manage all MCP clients.                       
    - Uses AsyncExitStack to manage async context for all clients.                    
    - Loads all active MCP clients from the manager.                                  
    - Optionally, loads additional MCP clients from CLI arguments (server scripts).   
    - Ensures at least one client is loaded, else raises RuntimeError.                
    - Creates a CliChat instance with the doc_client, all clients, and LLM service.   
    - Creates a CliApp instance for the CLI interface, initializes it.                
    - Prints status of loaded MCPs (if supported by manager).                         
    - Runs the CLI event loop (await cli.run()).                                      
                                                                                      
 7. Note: The entry point (calling main()) is handled by the root main.py file,       
    not here.                                                                         
                                                                                      
 In summary:                                                                          
    - This script loads config, validates it, initializes the LLM service,            
      loads MCP clients (from config and CLI), sets up the CLI chat interface,        
      and runs the main CLI event loop.                                               
'''

def check_llm_provider_config():
    '''
        Use a hashmap to dynamically check the provider config, 
        so adding new providers is easy and not hardcoded with if-else.
    '''
    # Each provider maps to a list of (value, error_message) tuples to check
    provider_checks = {
        claude_provider: [
            (claude_model, "Error: CLAUDE_MODEL cannot be empty when using Claude. Update .env"),
            (anthropic_api_key, "Error: ANTHROPIC_API_KEY cannot be empty when using Claude. Update .env"),
        ],
        gemini_provider: [
            (gemini_api_key, "Error: GEMINI_API_KEY cannot be empty when using Gemini. Update .env"),
        ],
    }
    if llm_provider in provider_checks:
        for value, error_msg in provider_checks[llm_provider]:
            assert value, error_msg
    else:
        raise ValueError(f"Unsupported LLM_PROVIDER: {llm_provider}. Use '{claude_provider}' or '{gemini_provider}'")

# Call the function to check config
check_llm_provider_config()

def initialize_llm_service_based_on_llm_provider(llm_provider):
    '''
        Helper function to initialize llm service based on llm provider, 
            + add a hashmap so when we want to add more provider + service --> just need 
              to add to hashmap, no need for hard-coding one more if else statment 
    '''
    llm_service_map = {
        claude_provider : Claude(model=claude_model),
        gemini_provider : Gemini(model=gemini_model, api_key=gemini_api_key),
    }
    if llm_provider in llm_service_map:
        return llm_service_map[llm_provider]
    else:
        raise ValueError(f"Unsupported LLM provider: {llm_provider}")

async def main():
    # Initialize LLM service based on provider
    llm_service = initialize_llm_service_based_on_llm_provider(llm_provider)

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
        
        # Optionally start additional server scripts passed via CLI
        server_scripts = sys.argv[1:]

        # Add any additional server scripts from command line
        for i, server_script in enumerate(server_scripts):
            client_id = f"client_{i}_{server_script}"
            client = await stack.enter_async_context(
                MCPClient(command="uv", args=["run", server_script])
            )
            clients[client_id] = client

        # Ensure at least one client is available
        if not clients:
            raise RuntimeError(
                "No MCP clients loaded. Configure MCPs in config/mcp_config.yaml or pass server scripts."
            )

        # Create chat with all clients
        doc_client = next(iter(clients.values()))
        chat = CliChat(
            doc_client=doc_client,
            clients=clients,
            llm_service=llm_service,
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


# Entry point is now handled by the root main.py file
