"""
Complete MCP-llmgine Integration Example

This example demonstrates how to integrate MCP tools with the llmgine message bus
system using the message bridge. It shows:

1. Setting up MCP servers and clients
2. Configuring the message bridge
3. Registering event handlers
4. Executing tools through the message bus
5. Monitoring execution lifecycle
6. Handling events and errors

This example can be run standalone or integrated into existing llmgine applications.
"""

import asyncio
import logging
import sys
import os
from typing import Dict, Any, Optional
from datetime import datetime

# Add project root to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# MCP and any-mcp imports
from any_mcp.managers.manager import MCPManager
from any_mcp.integration.message_bridge import (
    MCPMessageBridge,
    create_bridge_with_bus,
    create_standalone_bridge,
    MCPToolRegisteredEvent,
    MCPToolExecutionStartedEvent,
    MCPToolExecutionCompletedEvent,
    MCPServerConnectionEvent,
    ExecuteMCPToolCommand
)
from any_mcp.integration.event_handlers import (
    MCPEventHandlers,
    MCPEventHandlerRegistry,
    setup_event_registry_with_defaults,
    create_logging_error_handler
)

# Optional llmgine imports
try:
    from llmgine.bus.bus import MessageBus
    from llmgine.llm import SessionID
    LLMGINE_AVAILABLE = True
    print("✅ llmgine is available - using full integration")
except ImportError:
    LLMGINE_AVAILABLE = False
    print("⚠️  llmgine not available - using standalone mode")
    # Mock classes for standalone mode
    class MessageBus:
        pass
    class SessionID:
        def __init__(self, value):
            self.value = value

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class IntegrationExample:
    """
    Complete integration example showing MCP-llmgine bridge usage.
    
    This class demonstrates the full integration workflow from setup
    to execution and monitoring.
    """
    
    def __init__(self):
        self.mcp_manager: Optional[MCPManager] = None
        self.message_bus: Optional[MessageBus] = None
        self.message_bridge: Optional[MCPMessageBridge] = None
        self.event_handlers: Optional[MCPEventHandlers] = None
        self.event_registry: Optional[MCPEventHandlerRegistry] = None
        self.session_id = SessionID("EXAMPLE_SESSION")
    
    async def setup_mcp_manager(self) -> MCPManager:
        """Set up the MCP manager with example servers."""
        logger.info("Setting up MCP manager...")
        
        # Create MCP manager
        self.mcp_manager = MCPManager()
        
        # Add example MCP servers (adjust paths as needed)
        example_configs = [
            {
                "name": "calculator",
                "command": "python", 
                "args": ["mcps/demo_calculator.py"],
                "env": {}
            }
        ]
        
        # Start MCP servers
        for config in example_configs:
            try:
                await self.mcp_manager.start_mcp(
                    config["name"],
                    config["command"],
                    config["args"],
                    config.get("env", {})
                )
                logger.info(f"✅ Started MCP server: {config['name']}")
            except Exception as e:
                logger.warning(f"❌ Failed to start MCP server {config['name']}: {e}")
        
        return self.mcp_manager
    
    async def setup_message_bus(self) -> Optional[MessageBus]:
        """Set up the llmgine message bus (if available)."""
        if not LLMGINE_AVAILABLE:
            logger.info("Skipping message bus setup - llmgine not available")
            return None
        
        logger.info("Setting up llmgine message bus...")
        
        try:
            self.message_bus = MessageBus()
            await self.message_bus.start()
            logger.info("✅ Message bus started successfully")
            return self.message_bus
        except Exception as e:
            logger.error(f"❌ Failed to start message bus: {e}")
            return None
    
    def setup_event_handlers(self):
        """Set up event handlers for monitoring and logging."""
        logger.info("Setting up event handlers...")
        
        # Create event handlers
        self.event_handlers = MCPEventHandlers()
        
        # Create event registry
        self.event_registry = setup_event_registry_with_defaults()
        
        # Add custom event handlers
        self.event_registry.register_handler(
            "MCPToolRegisteredEvent",
            self.on_tool_registered,
            "custom_registration_handler"
        )
        
        self.event_registry.register_handler(
            "MCPToolExecutionStartedEvent", 
            self.on_execution_started,
            "custom_execution_start_handler"
        )
        
        self.event_registry.register_handler(
            "MCPToolExecutionCompletedEvent",
            self.on_execution_completed,
            "custom_execution_complete_handler"
        )
        
        # Add error handler
        self.event_registry.add_error_handler(create_logging_error_handler())
        
        logger.info("✅ Event handlers configured")
    
    async def setup_message_bridge(self):
        """Set up the message bridge."""
        logger.info("Setting up message bridge...")
        
        if not self.mcp_manager:
            raise RuntimeError("MCP manager must be set up first")
        
        if LLMGINE_AVAILABLE and self.message_bus:
            # Full integration with llmgine
            self.message_bridge = create_bridge_with_bus(
                self.mcp_manager,
                self.message_bus,
                self.session_id.value
            )
            logger.info("✅ Message bridge created with llmgine integration")
        else:
            # Standalone mode
            self.message_bridge = create_standalone_bridge(self.mcp_manager)
            logger.info("✅ Message bridge created in standalone mode")
        
        # Register event handlers with the bridge
        if self.event_handlers:
            self.message_bridge.add_event_handler(
                MCPToolRegisteredEvent,
                self.event_handlers.handle_tool_registered
            )
            self.message_bridge.add_event_handler(
                MCPToolExecutionStartedEvent,
                self.event_handlers.handle_execution_started
            )
            self.message_bridge.add_event_handler(
                MCPToolExecutionCompletedEvent,
                self.event_handlers.handle_execution_completed
            )
            self.message_bridge.add_event_handler(
                MCPServerConnectionEvent,
                self.event_handlers.handle_server_connection
            )
    
    async def register_all_tools(self):
        """Register all available MCP tools."""
        if not self.message_bridge:
            raise RuntimeError("Message bridge must be set up first")
        
        logger.info("Registering all available MCP tools...")
        
        try:
            await self.message_bridge.register_all_tools(self.session_id)
            
            # Get registered tools
            if self.event_handlers:
                tools = self.event_handlers.get_registered_tools()
                logger.info(f"✅ Registered {len(tools)} tools:")
                for tool_key, tool_info in tools.items():
                    logger.info(f"  - {tool_key}")
        except Exception as e:
            logger.error(f"❌ Failed to register tools: {e}")
    
    async def demonstrate_tool_execution(self):
        """Demonstrate tool execution through the message bridge."""
        if not self.message_bridge:
            raise RuntimeError("Message bridge must be set up first")
        
        logger.info("Demonstrating tool execution...")
        
        # Example 1: Calculator tool (if available)
        try:
            result = await self.message_bridge.execute_tool(
                mcp_name="calculator",
                tool_name="add",
                arguments={"a": 5, "b": 3},
                session_id=self.session_id
            )
            
            if result["success"]:
                logger.info(f"✅ Calculator add(5, 3) = {result['result']}")
            else:
                logger.error(f"❌ Calculator execution failed: {result['error']}")
                
        except Exception as e:
            logger.warning(f"Calculator tool not available or failed: {e}")
        
        # Example 2: List available tools
        try:
            if LLMGINE_AVAILABLE and self.message_bus:
                from any_mcp.integration.message_bridge import ListMCPToolsCommand
                
                command = ListMCPToolsCommand(session_id=self.session_id)
                result = await self.message_bus.execute(command)
                
                if result.success:
                    tools = result.data.get("tools", [])
                    logger.info(f"✅ Found {len(tools)} available tools")
                    for tool in tools[:3]:  # Show first 3 tools
                        logger.info(f"  - {tool['mcp_name']}:{tool['tool_name']}")
            else:
                # Standalone mode
                tools = self.message_bridge.tool_adapter.list_available_tools()
                logger.info(f"✅ Found {len(tools)} available tools (standalone mode)")
                
        except Exception as e:
            logger.error(f"❌ Failed to list tools: {e}")
    
    async def demonstrate_monitoring(self):
        """Demonstrate monitoring and metrics collection."""
        if not self.event_handlers:
            logger.warning("Event handlers not available for monitoring")
            return
        
        logger.info("Demonstrating monitoring capabilities...")
        
        # Get execution metrics
        metrics = self.event_handlers.get_execution_metrics()
        logger.info("📊 Execution Metrics:")
        logger.info(f"  Total executions: {metrics['total_executions']}")
        logger.info(f"  Successful: {metrics['successful_executions']}")
        logger.info(f"  Failed: {metrics['failed_executions']}")
        logger.info(f"  Average time: {metrics['avg_execution_time_ms']:.2f}ms")
        
        # Get registered tools
        tools = self.event_handlers.get_registered_tools()
        logger.info(f"📋 Registered tools: {len(tools)}")
        
        # Get active executions
        if self.message_bridge:
            active = self.message_bridge.get_active_executions()
            logger.info(f"🔄 Active executions: {len(active)}")
        
        # Get event registry stats
        if self.event_registry:
            stats = self.event_registry.get_stats()
            logger.info("📈 Event Registry Stats:")
            logger.info(f"  Total handlers: {stats['total_handlers']}")
            logger.info(f"  Event types: {len(stats['event_types'])}")
    
    # Custom event handlers
    async def on_tool_registered(self, event: MCPToolRegisteredEvent):
        """Custom handler for tool registration events."""
        logger.info(f"🔧 Tool registered: {event.mcp_name}:{event.tool_name}")
    
    async def on_execution_started(self, event: MCPToolExecutionStartedEvent):
        """Custom handler for execution start events."""
        logger.info(f"▶️  Execution started: {event.execution_id} ({event.tool_name})")
    
    async def on_execution_completed(self, event: MCPToolExecutionCompletedEvent):
        """Custom handler for execution completion events."""
        status = "✅ SUCCESS" if event.success else "❌ FAILED"
        duration = f"{event.execution_time_ms:.2f}ms" if event.execution_time_ms else "unknown"
        logger.info(f"⏹️  Execution completed: {event.execution_id} - {status} ({duration})")
        
        if not event.success and event.error_message:
            logger.error(f"   Error: {event.error_message}")
    
    async def cleanup(self):
        """Clean up all resources."""
        logger.info("Cleaning up resources...")
        
        try:
            # Clean up message bridge
            if self.message_bridge:
                await self.message_bridge.cleanup()
            
            # Clean up event handlers
            if self.event_handlers:
                await self.event_handlers.cleanup()
            
            # Stop message bus
            if self.message_bus and LLMGINE_AVAILABLE:
                await self.message_bus.stop()
            
            # Clean up MCP manager
            if self.mcp_manager:
                await self.mcp_manager.cleanup()
            
            logger.info("✅ Cleanup completed")
            
        except Exception as e:
            logger.error(f"❌ Error during cleanup: {e}")
    
    async def run_complete_example(self):
        """Run the complete integration example."""
        logger.info("🚀 Starting MCP-llmgine Integration Example")
        logger.info("=" * 50)
        
        try:
            # Setup phase
            logger.info("📋 Phase 1: Setup")
            await self.setup_mcp_manager()
            await self.setup_message_bus()
            self.setup_event_handlers()
            await self.setup_message_bridge()
            
            # Registration phase
            logger.info("\n📋 Phase 2: Tool Registration")
            await self.register_all_tools()
            
            # Execution phase
            logger.info("\n📋 Phase 3: Tool Execution")
            await self.demonstrate_tool_execution()
            
            # Wait a bit for events to process
            await asyncio.sleep(1)
            
            # Monitoring phase
            logger.info("\n📋 Phase 4: Monitoring & Metrics")
            await self.demonstrate_monitoring()
            
            logger.info("\n✅ Integration example completed successfully!")
            
        except Exception as e:
            logger.error(f"❌ Integration example failed: {e}")
            raise
        finally:
            await self.cleanup()


async def main():
    """Main entry point for the integration example."""
    example = IntegrationExample()
    
    try:
        await example.run_complete_example()
    except KeyboardInterrupt:
        logger.info("🛑 Example interrupted by user")
        await example.cleanup()
    except Exception as e:
        logger.error(f"💥 Example failed with error: {e}")
        await example.cleanup()
        sys.exit(1)


def run_basic_example():
    """Run a basic example without llmgine integration."""
    print("🔧 Running basic MCP integration example...")
    
    async def basic_example():
        # Create MCP manager
        manager = MCPManager()
        
        try:
            # Start a simple calculator MCP server
            await manager.start_mcp(
                "calculator",
                "python",
                ["mcps/demo_calculator.py"],
                {}
            )
            
            # Create standalone bridge
            bridge = create_standalone_bridge(manager)
            
            # Execute a tool
            result = await bridge.execute_tool(
                "calculator",
                "add", 
                {"a": 10, "b": 5}
            )
            
            print(f"Result: {result}")
            
        except Exception as e:
            print(f"Basic example failed: {e}")
        finally:
            await manager.cleanup()
    
    asyncio.run(basic_example())


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--basic":
        run_basic_example()
    else:
        asyncio.run(main())
