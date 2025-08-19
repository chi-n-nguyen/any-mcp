"""
MCP-Enhanced Tool Chat Engine

This is an enhanced version of the tool_chat_engine that uses the MCP (Model Context Protocol)
system for tool management instead of the original ToolManager. It provides:

- Seamless integration with MCP servers
- Enhanced tool discovery and execution
- Event-driven tool lifecycle management
- Backwards compatibility with existing tool registration patterns
- Rich monitoring and metrics collection
"""

import asyncio
import json
import uuid
from dataclasses import dataclass
from typing import Any, List, Dict, Optional

from litellm import acompletion

from llmgine.bus.bus import MessageBus
from llmgine.llm import AsyncOrSyncToolFunction, SessionID
from llmgine.llm.context.memory import SimpleChatHistory
from llmgine.llm.tools import ToolCall
from llmgine.messages.commands import Command, CommandResult
from llmgine.messages.events import Event
from llmgine.ui.cli.cli import EngineCLI
from llmgine.ui.cli.components import EngineResultComponent

# Import our MCP components
from llmgine.llm.tools.mcp_tool_manager import MCPToolManager, MCPServerConfig, create_default_mcp_servers
from llmgine.llm.tools.mcp_bridge_integration import (
    LLMgineMCPBridge,
    create_llmgine_mcp_integration,
    get_default_mcp_servers,
    MCPToolExecutionLLMgineEvent,
    MCPToolRegisteredLLMgineEvent
)


@dataclass
class MCPToolChatEngineCommand(Command):
    """Command for the MCP Tool Chat Engine."""
    prompt: str = ""


@dataclass
class MCPToolChatEngineStatusEvent(Event):
    """Status event for the MCP Tool Chat Engine."""
    status: str = ""
    tool_info: Dict[str, Any] = None
    
    def __post_init__(self):
        super().__post_init__()
        if self.tool_info is None:
            self.tool_info = {}


# ==================== Example Tools (for backwards compatibility) ====================

def get_weather(city: str) -> str:
    """Get the current weather for a city.
    
    Args:
        city: The name of the city to get weather for
    """
    # Mock weather data
    weather_data = {
        "New York": "Sunny, 72°F",
        "London": "Cloudy, 15°C", 
        "Tokyo": "Rainy, 18°C",
        "Sydney": "Partly cloudy, 22°C"
    }
    
    return weather_data.get(city, f"Weather data not available for {city}")


def calculate(expression: str) -> str:
    """Calculate a mathematical expression.
    
    Args:
        expression: Mathematical expression to evaluate
    """
    try:
        # Safe evaluation of basic math expressions
        result = eval(expression, {"__builtins__": {}}, {
            "abs": abs, "round": round, "min": min, "max": max,
            "sum": sum, "pow": pow, "sqrt": lambda x: x**0.5
        })
        return str(result)
    except Exception as e:
        return f"Error calculating '{expression}': {str(e)}"


def search_web(query: str) -> str:
    """Search the web for information.
    
    Args:
        query: Search query
    """
    return f"Mock search results for: {query}"


def play_music(song: str, artist: str = "") -> str:
    """Play a music track.
    
    Args:
        song: Name of the song
        artist: Artist name (optional)
    """
    return f"Now playing '{song}'" + (f" by {artist}" if artist else "")


# ==================== MCP Tool Chat Engine ====================

class MCPToolChatEngine:
    """
    Enhanced Tool Chat Engine using MCP for tool management.
    
    This engine provides all the functionality of the original ToolChatEngine
    but with enhanced capabilities through the MCP system:
    - Dynamic tool discovery from MCP servers
    - Enhanced monitoring and metrics
    - Event-driven tool lifecycle management
    - Seamless integration with external tool providers
    """
    
    def __init__(
        self,
        model: str = "gpt-4o-mini",
        session_id: str = None,
        enable_mcp_servers: bool = True,
        mcp_server_configs: Optional[List[MCPServerConfig]] = None
    ):
        self.session_id = SessionID(session_id or str(uuid.uuid4()))
        self.bus = MessageBus()
        self.model = model
        self.enable_mcp_servers = enable_mcp_servers

        # Initialize chat history
        self.chat_history = SimpleChatHistory()
        self.chat_history.set_system_prompt(
            "You are a helpful assistant with access to various tools including "
            "web search, calculations, weather information, and external services "
            "through MCP (Model Context Protocol) servers. "
            "Use the tools when appropriate to help answer user questions."
        )

        # Initialize MCP tool manager
        self.tool_manager = MCPToolManager(self.chat_history, str(self.session_id))
        
        # Initialize MCP bridge integration
        self.mcp_bridge: Optional[LLMgineMCPBridge] = None
        
        # Store server configs
        self.mcp_server_configs = mcp_server_configs or (
            create_default_mcp_servers() if enable_mcp_servers else []
        )
        
        # Track initialization
        self._initialized = False

    async def initialize(self):
        """Initialize the MCP system and register tools."""
        if self._initialized:
            return
        
        try:
            # Initialize MCP tool manager
            await self.tool_manager.initialize()
            
            # Register local tools first (for backwards compatibility)
            self._register_local_tools()
            
            # Set up MCP bridge integration if enabled
            if self.enable_mcp_servers:
                await self._setup_mcp_integration()
            
            # Register MCP servers
            if self.mcp_server_configs:
                await self._register_mcp_servers()
            
            # Register event handlers
            self._register_event_handlers()
            
            self._initialized = True
            
            # Log initialization summary
            await self._log_initialization_summary()
            
        except Exception as e:
            await self.bus.publish(
                MCPToolChatEngineStatusEvent(
                    status=f"initialization failed: {str(e)}",
                    session_id=self.session_id
                )
            )
            raise

    def _register_local_tools(self):
        """Register local tools for backwards compatibility."""
        local_tools = [get_weather, calculate, search_web, play_music]
        
        for tool in local_tools:
            self.tool_manager.register_tool(tool)
        
        print(f"Registered {len(local_tools)} local tools")

    async def _setup_mcp_integration(self):
        """Set up MCP bridge integration with llmgine MessageBus."""
        try:
            # Create MCP bridge integration
            mcp_servers = [
                {
                    "name": config.name,
                    "command": config.command,
                    "args": config.args,
                    "env": config.env
                }
                for config in self.mcp_server_configs
            ]
            
            self.mcp_bridge = await create_llmgine_mcp_integration(
                self.bus,
                str(self.session_id),
                mcp_servers
            )
            
            print("MCP bridge integration initialized")
            
        except Exception as e:
            print(f"Warning: MCP bridge integration failed: {e}")
            # Continue without MCP bridge - local tools will still work

    async def _register_mcp_servers(self):
        """Register MCP servers with the tool manager."""
        results = await self.tool_manager.register_mcp_servers(self.mcp_server_configs)
        
        successful = sum(1 for success in results.values() if success)
        total = len(results)
        
        await self.bus.publish(
            MCPToolChatEngineStatusEvent(
                status=f"registered {successful}/{total} MCP servers",
                tool_info={"servers": results},
                session_id=self.session_id
            )
        )

    def _register_event_handlers(self):
        """Register event handlers for MCP events."""
        # Register handler for tool execution events
        self.bus.register_event_handler(
            MCPToolExecutionLLMgineEvent,
            self._handle_tool_execution_event,
            self.session_id
        )
        
        # Register handler for tool registration events
        self.bus.register_event_handler(
            MCPToolRegisteredLLMgineEvent,
            self._handle_tool_registered_event,
            self.session_id
        )

    async def _handle_tool_execution_event(self, event: MCPToolExecutionLLMgineEvent):
        """Handle MCP tool execution events."""
        if event.success:
            await self.bus.publish(
                MCPToolChatEngineStatusEvent(
                    status=f"tool executed: {event.tool_name}",
                    tool_info={
                        "tool": event.tool_name,
                        "mcp_server": event.mcp_name,
                        "execution_time": event.execution_time_ms
                    },
                    session_id=self.session_id
                )
            )
        else:
            await self.bus.publish(
                MCPToolChatEngineStatusEvent(
                    status=f"tool failed: {event.tool_name} - {event.error_message}",
                    tool_info={
                        "tool": event.tool_name,
                        "mcp_server": event.mcp_name,
                        "error": event.error_message
                    },
                    session_id=self.session_id
                )
            )

    async def _handle_tool_registered_event(self, event: MCPToolRegisteredLLMgineEvent):
        """Handle MCP tool registration events."""
        await self.bus.publish(
            MCPToolChatEngineStatusEvent(
                status=f"tool registered: {event.mcp_name}:{event.tool_name}",
                tool_info={
                    "tool": event.tool_name,
                    "mcp_server": event.mcp_name,
                    "schema": event.tool_schema
                },
                session_id=self.session_id
            )
        )

    async def _log_initialization_summary(self):
        """Log initialization summary."""
        try:
            # Get tool counts
            local_tools = len(self.tool_manager.local_tools)
            total_schemas = len(self.tool_manager.tool_schemas)
            
            # Get MCP server status
            mcp_status = await self.tool_manager.get_mcp_server_status()
            active_servers = sum(1 for status in mcp_status.values() if status["active"])
            
            # Get available MCP tools
            mcp_tools = await self.tool_manager.discover_mcp_tools()
            
            summary = {
                "local_tools": local_tools,
                "mcp_servers": len(mcp_status),
                "active_servers": active_servers,
                "mcp_tools": len(mcp_tools),
                "total_tool_schemas": total_schemas
            }
            
            await self.bus.publish(
                MCPToolChatEngineStatusEvent(
                    status="initialization complete",
                    tool_info=summary,
                    session_id=self.session_id
                )
            )
            
            print(f"MCPToolChatEngine initialized:")
            print(f"  - {local_tools} local tools")
            print(f"  - {active_servers}/{len(mcp_status)} MCP servers active")
            print(f"  - {len(mcp_tools)} MCP tools available")
            print(f"  - {total_schemas} total tool schemas")
            
        except Exception as e:
            print(f"Warning: Failed to generate initialization summary: {e}")

    async def handle_command(self, command: MCPToolChatEngineCommand) -> CommandResult:
        """Handle chat command with tool support."""
        # Ensure initialization
        if not self._initialized:
            await self.initialize()
        
        try:
            await self.bus.publish(
                MCPToolChatEngineStatusEvent(
                    status="processing", session_id=self.session_id
                )
            )

            # Add user message to history
            self.chat_history.add_user_message(command.prompt)

            # Get current context
            messages = self.tool_manager.chat_history_to_messages()

            # Get initial response
            await self.bus.publish(
                MCPToolChatEngineStatusEvent(
                    status="calling LLM", session_id=self.session_id
                )
            )

            response = await acompletion(
                model=self.model,
                messages=messages,
                tools=self.tool_manager.tool_schemas,
                tool_choice="auto"
            )

            if not response.choices:
                return CommandResult(success=False, error="No response from LLM")

            message = response.choices[0].message

            # Check for tool calls
            if hasattr(message, "tool_calls") and message.tool_calls:
                await self.bus.publish(
                    MCPToolChatEngineStatusEvent(
                        status="executing tools",
                        tool_info={"tool_count": len(message.tool_calls)},
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

                # Execute tools through MCP tool manager
                tool_results = await self.tool_manager.execute_tool_calls(tool_calls)

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
                        status="getting final response", session_id=self.session_id
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
                            status="finished", session_id=self.session_id
                        )
                    )
                    return CommandResult(success=True, result=final_content)
            else:
                # No tool calls, just return the response
                content = message.content or ""
                self.chat_history.add_assistant_message(content)

                await self.bus.publish(
                    MCPToolChatEngineStatusEvent(
                        status="finished", session_id=self.session_id
                    )
                )
                return CommandResult(success=True, result=content)

        except Exception as e:
            await self.bus.publish(
                MCPToolChatEngineStatusEvent(
                    status=f"error: {str(e)}", session_id=self.session_id
                )
            )
            return CommandResult(success=False, error=str(e))

    # ==================== Additional Methods ====================

    async def register_tool(self, func: AsyncOrSyncToolFunction) -> None:
        """Register a new tool (maintains backwards compatibility)."""
        if not self._initialized:
            await self.initialize()
        
        self.tool_manager.register_tool(func)
        
        await self.bus.publish(
            MCPToolChatEngineStatusEvent(
                status=f"registered tool: {func.__name__}",
                tool_info={"tool": func.__name__, "type": "local"},
                session_id=self.session_id
            )
        )

    async def add_mcp_server(self, config: MCPServerConfig) -> bool:
        """Add a new MCP server dynamically."""
        if not self._initialized:
            await self.initialize()
        
        success = await self.tool_manager.register_mcp_server(config)
        
        if success:
            await self.bus.publish(
                MCPToolChatEngineStatusEvent(
                    status=f"added MCP server: {config.name}",
                    tool_info={"server": config.name, "command": config.command},
                    session_id=self.session_id
                )
            )
        
        return success

    async def get_available_tools(self) -> Dict[str, Any]:
        """Get information about all available tools."""
        if not self._initialized:
            await self.initialize()
        
        local_tools = list(self.tool_manager.local_tools.keys())
        mcp_tools = await self.tool_manager.discover_mcp_tools()
        server_status = await self.tool_manager.get_mcp_server_status()
        
        return {
            "local_tools": local_tools,
            "mcp_tools": mcp_tools,
            "mcp_servers": server_status,
            "total_schemas": len(self.tool_manager.tool_schemas)
        }

    async def get_metrics(self) -> Dict[str, Any]:
        """Get execution metrics and statistics."""
        if not self._initialized:
            return {}
        
        metrics = {}
        
        # Get MCP bridge metrics if available
        if self.mcp_bridge:
            try:
                mcp_metrics = await self.mcp_bridge.get_mcp_metrics()
                metrics["mcp"] = mcp_metrics
            except Exception as e:
                print(f"Warning: Failed to get MCP metrics: {e}")
        
        # Get tool manager status
        try:
            tool_info = await self.get_available_tools()
            metrics["tools"] = tool_info
        except Exception as e:
            print(f"Warning: Failed to get tool info: {e}")
        
        return metrics

    async def cleanup(self):
        """Clean up resources."""
        try:
            if self.mcp_bridge:
                await self.mcp_bridge.cleanup()
            
            if self.tool_manager:
                await self.tool_manager.cleanup()
            
            # Unregister event handlers
            self.bus.unregister_session_handlers(self.session_id)
            
            print("MCPToolChatEngine cleanup completed")
            
        except Exception as e:
            print(f"Error during cleanup: {e}")


# ==================== Main Function ====================

async def main():
    """Main function to run the MCP Tool Chat Engine."""
    print("🚀 Starting MCP Tool Chat Engine...")
    
    # Create engine with default MCP servers
    engine = MCPToolChatEngine(
        model="gpt-4o-mini",
        enable_mcp_servers=True
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

