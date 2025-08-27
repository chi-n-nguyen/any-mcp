"""
MCP-Enhanced Tool Chat Engine

This is an enhanced version of the tool_chat_engine that demonstrates
the integration with the MCP (Model Context Protocol) system.
"""

import asyncio
import json
import uuid
from dataclasses import dataclass
from typing import Any

from litellm import acompletion

from llmgine.bus.bus import MessageBus
from llmgine.llm import AsyncOrSyncToolFunction, SessionID
from llmgine.llm.context.memory import SimpleChatHistory
from llmgine.llm.tools import ToolCall
from llmgine.llm.tools.enhanced_tool_manager import (
    EnhancedToolManager, 
    MCPServerConfig,
    create_enhanced_tool_manager_with_servers,
    get_default_mcp_servers
)
from llmgine.messages.commands import Command, CommandResult
from llmgine.messages.events import Event
from llmgine.ui.cli.cli import EngineCLI
from llmgine.ui.cli.components import EngineResultComponent


@dataclass
class MCPToolChatEngineCommand(Command):
    """Command for the MCP-Enhanced Tool Chat Engine."""
    prompt: str = ""


@dataclass
class MCPToolChatEngineStatusEvent(Event):
    """Status event for the MCP-Enhanced Tool Chat Engine."""
    status: str = ""
    details: str = ""


# Example local tools (for demonstration)
def get_weather(city: str) -> str:
    """Get the current weather for a given city."""
    # Mock implementation
    weather_data = {
        "New York": "Sunny, 72°F",
        "London": "Cloudy, 15°C",
        "Tokyo": "Rainy, 18°C",
        "Paris": "Partly cloudy, 20°C"
    }
    return weather_data.get(city, f"Weather data not available for {city}")


def calculate_local(expression: str) -> str:
    """Calculate a mathematical expression locally."""
    try:
        # Safe evaluation of basic math expressions
        result = eval(expression, {"__builtins__": {}}, {
            "abs": abs, "round": round, "min": min, "max": max,
            "sum": sum, "pow": pow
        })
        return f"The result of {expression} is {result}"
    except Exception as e:
        return f"Error calculating {expression}: {str(e)}"


async def search_web(query: str) -> str:
    """Search the web for information."""
    # Mock implementation
    await asyncio.sleep(0.1)  # Simulate network delay
    return f"Mock search results for '{query}': Found relevant information about {query}"


def play_music(song: str, artist: str = "") -> str:
    """Play a music track."""
    artist_part = f" by {artist}" if artist else ""
    return f"Now playing '{song}'{artist_part}"


class MCPEnhancedToolChatEngine:
    """
    Enhanced Tool Chat Engine with MCP integration.
    
    This engine demonstrates:
    - Backward compatibility with local tools
    - Integration with MCP servers for external tools
    - Unified tool execution through enhanced ToolManager
    - Rich status reporting and error handling
    """
    
    def __init__(self, model: str = "gpt-4o-mini", session_id: str = None, enable_mcp: bool = True):
        self.session_id = SessionID(session_id or str(uuid.uuid4()))
        self.bus = MessageBus()
        self.model = model
        self.enable_mcp = enable_mcp

        # Initialize chat history
        self.chat_history = SimpleChatHistory()
        self.chat_history.set_system_prompt(
            "You are a helpful assistant with access to various tools. "
            "You can perform calculations, get weather information, search the web, "
            "and access external services through MCP servers. "
            "Use the tools when appropriate to help answer user questions."
        )

        # Tool manager will be initialized in setup
        self.tool_manager: Optional[EnhancedToolManager] = None
        self._initialized = False
    
    async def initialize(self):
        """Initialize the engine and set up tools."""
        if self._initialized:
            return
        
        await self.bus.publish(
            MCPToolChatEngineStatusEvent(
                status="initializing",
                details="Setting up enhanced tool manager",
                session_id=self.session_id
            )
        )
        
        try:
            # Create enhanced tool manager
            if self.enable_mcp:
                # Get default MCP servers
                mcp_servers = get_default_mcp_servers()
                
                # Add custom MCP servers (you can extend this)
                custom_servers = [
                    # Add more servers as needed
                ]
                mcp_servers.extend(custom_servers)
                
                self.tool_manager = await create_enhanced_tool_manager_with_servers(
                    self.chat_history,
                    mcp_servers
                )
            else:
                # Use enhanced manager without MCP
                self.tool_manager = EnhancedToolManager(self.chat_history)
            
            # Register local tools
            self._register_local_tools()
            
            # Get tool information
            tools_info = await self.tool_manager.list_all_tools()
            
            await self.bus.publish(
                MCPToolChatEngineStatusEvent(
                    status="initialized",
                    details=f"Ready with {len(tools_info['local_tools'])} local tools, "
                           f"{len(tools_info['mcp_tools'])} MCP tools, "
                           f"{len(tools_info['mcp_servers'])} MCP servers",
                    session_id=self.session_id
                )
            )
            
            self._initialized = True
            
            # Print initialization summary
            print(f"\n🚀 MCP-Enhanced Tool Chat Engine Initialized")
            print(f"   Local tools: {len(tools_info['local_tools'])}")
            print(f"   MCP tools: {len(tools_info['mcp_tools'])}")
            print(f"   MCP servers: {len(tools_info['mcp_servers'])}")
            print(f"   Total schemas: {tools_info['total_schemas']}")
            
            if tools_info['mcp_servers']:
                print("   Active MCP servers:")
                for server_name, status in tools_info['mcp_servers'].items():
                    status_icon = "✅" if status else "❌"
                    print(f"     {status_icon} {server_name}")
            
        except Exception as e:
            await self.bus.publish(
                MCPToolChatEngineStatusEvent(
                    status="initialization_failed",
                    details=f"Failed to initialize: {str(e)}",
                    session_id=self.session_id
                )
            )
            raise
    
    def _register_local_tools(self):
        """Register local tools with the tool manager."""
        local_tools = [get_weather, calculate_local, search_web, play_music]
        
        for tool in local_tools:
            self.tool_manager.register_tool(tool)
        
        print(f"   Registered {len(local_tools)} local tools")
    
    async def handle_command(self, command: MCPToolChatEngineCommand) -> CommandResult:
        """Handle chat command with enhanced tool support."""
        # Ensure initialization
        if not self._initialized:
            await self.initialize()
        
        try:
            await self.bus.publish(
                MCPToolChatEngineStatusEvent(
                    status="processing",
                    details=f"Processing prompt: {command.prompt[:50]}...",
                    session_id=self.session_id
                )
            )

            # Add user message to history
            self.chat_history.add_user_message(command.prompt)

            # Get current context
            messages = self.tool_manager.chat_history_to_messages()

            # Get initial response
            await self.bus.publish(
                MCPToolChatEngineStatusEvent(
                    status="calling_llm",
                    details="Getting response from language model",
                    session_id=self.session_id
                )
            )

            response = await acompletion(
                model=self.model,
                messages=messages,
                tools=self.tool_manager.parse_tools_to_list(),
                tool_choice="auto"
            )

            if not response.choices:
                return CommandResult(success=False, error="No response from LLM")

            message = response.choices[0].message

            # Check for tool calls
            if hasattr(message, "tool_calls") and message.tool_calls:
                tool_count = len(message.tool_calls)
                await self.bus.publish(
                    MCPToolChatEngineStatusEvent(
                        status="executing_tools",
                        details=f"Executing {tool_count} tool call(s)",
                        session_id=self.session_id
                    )
                )

                # Convert litellm tool calls to our ToolCall format
                tool_calls = [
                    ToolCall(
                        id=tc.id, name=tc.function.name, arguments=tc.function.arguments
                    )
                    for tc in message.tool_calls
                ]

                # Execute tools
                tool_results = await self.tool_manager.execute_tool_calls(tool_calls)

                # Log tool execution results
                for tool_call, result in zip(tool_calls, tool_results):
                    tool_type = "MCP" if self.tool_manager.is_mcp_tool(tool_call.name) else "Local"
                    await self.bus.publish(
                        MCPToolChatEngineStatusEvent(
                            status="tool_executed",
                            details=f"{tool_type} tool '{tool_call.name}' executed",
                            session_id=self.session_id
                        )
                    )

                # Add assistant message with tool calls
                self.chat_history.add_assistant_message(
                    content=message.content or "", tool_calls=tool_calls
                )

                # Add tool results
                for tool_call, result in zip(tool_calls, tool_results):
                    self.chat_history.add_tool_message(
                        tool_call_id=tool_call.id, content=str(result)
                    )

                # Get final response after tool execution
                await self.bus.publish(
                    MCPToolChatEngineStatusEvent(
                        status="getting_final_response",
                        details="Getting final response after tool execution",
                        session_id=self.session_id
                    )
                )

                final_context = self.tool_manager.chat_history_to_messages()
                final_response = await acompletion(
                    model=self.model, messages=final_context
                )

                if final_response.choices:
                    final_content = final_response.choices[0].message.content
                    self.chat_history.add_assistant_message(final_content)

                    await self.bus.publish(
                        MCPToolChatEngineStatusEvent(
                            status="completed",
                            details="Response generated successfully",
                            session_id=self.session_id
                        )
                    )
                    return CommandResult(success=True, result=final_content)
            else:
                # No tool calls, just return the response
                content = message.content or ""
                self.chat_history.add_assistant_message(content)

                await self.bus.publish(
                    MCPToolChatEngineStatusEvent(
                        status="completed",
                        details="Response generated without tools",
                        session_id=self.session_id
                    )
                )
                return CommandResult(success=True, result=content)

        except Exception as e:
            await self.bus.publish(
                MCPToolChatEngineStatusEvent(
                    status="error",
                    details=f"Error: {str(e)}",
                    session_id=self.session_id
                )
            )
            return CommandResult(success=False, error=str(e))

    async def get_status(self) -> Dict[str, Any]:
        """Get current engine status."""
        if not self._initialized:
            return {"status": "not_initialized"}
        
        tools_info = await self.tool_manager.list_all_tools()
        server_status = await self.tool_manager.get_mcp_server_status()
        
        return {
            "status": "ready",
            "initialized": self._initialized,
            "mcp_enabled": self.enable_mcp,
            "tools": tools_info,
            "server_health": server_status
        }
    
    async def add_mcp_server(self, name: str, command: str, args: list, env: dict = None) -> bool:
        """Add a new MCP server dynamically."""
        if not self._initialized:
            await self.initialize()
        
        success = await self.tool_manager.add_mcp_server(name, command, args, env)
        
        if success:
            await self.bus.publish(
                MCPToolChatEngineStatusEvent(
                    status="mcp_server_added",
                    details=f"MCP server '{name}' added successfully",
                    session_id=self.session_id
                )
            )
        
        return success
    
    async def cleanup(self):
        """Clean up resources."""
        if self.tool_manager:
            await self.tool_manager.cleanup()


async def main():
    """Main function to run the MCP-Enhanced Tool Chat Engine."""
    print("🚀 Starting MCP-Enhanced Tool Chat Engine...")
    
    # Create engine
    engine = MCPEnhancedToolChatEngine(
        model="gpt-4o-mini",
        enable_mcp=True  # Enable MCP integration
    )
    
    try:
        # Initialize the engine
        await engine.initialize()
        
        # Create CLI
        cli = EngineCLI(session_id=str(engine.session_id))
        cli.register_engine(engine)
        cli.register_engine_command(
            MCPToolChatEngineCommand,
            engine.handle_command
        )
        
        # Add result component
        cli.add_component("result", EngineResultComponent())
        
        # Start CLI
        await cli.main()
        
    except KeyboardInterrupt:
        print("\n🛑 Interrupted by user")
    except Exception as e:
        print(f"💥 Error: {e}")
    finally:
        await engine.cleanup()
        print("👋 Goodbye!")


if __name__ == "__main__":
    asyncio.run(main())

