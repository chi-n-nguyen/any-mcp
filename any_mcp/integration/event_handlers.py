"""
Event Handlers for MCP-llmgine Integration

This module provides specialized event handlers for managing MCP tool execution
lifecycle events within the llmgine message bus system.
"""

import logging
import asyncio
from typing import Dict, Any, Optional, List, Callable
from datetime import datetime, timedelta

# llmgine imports (optional)
try:
    from llmgine.bus.interfaces import AsyncEventHandler
    from llmgine.messages.events import Event
    from llmgine.llm import SessionID
    LLMGINE_AVAILABLE = True
except ImportError:
    LLMGINE_AVAILABLE = False
    AsyncEventHandler = Callable
    class Event:
        pass
    class SessionID:
        pass

# Local imports
from any_mcp.integration.message_bridge import (
    MCPEvent,
    MCPToolRegisteredEvent,
    MCPToolExecutionStartedEvent,
    MCPToolExecutionCompletedEvent,
    MCPServerConnectionEvent
)

logger = logging.getLogger(__name__)


class MCPEventHandlerRegistry:
    """
    Registry for managing MCP event handlers with lifecycle management.
    
    This registry provides:
    - Automatic handler registration and cleanup
    - Event filtering and routing
    - Performance monitoring and metrics
    - Error handling and recovery
    """
    
    def __init__(self):
        self.handlers: Dict[str, List[AsyncEventHandler]] = {}
        self.handler_stats: Dict[str, Dict[str, Any]] = {}
        self.error_handlers: List[Callable[[Exception, Event], None]] = []
        
    def register_handler(
        self,
        event_type: str,
        handler: AsyncEventHandler,
        handler_id: Optional[str] = None
    ):
        """Register an event handler for a specific event type."""
        if event_type not in self.handlers:
            self.handlers[event_type] = []
            self.handler_stats[event_type] = {
                "total_events": 0,
                "successful_events": 0,
                "failed_events": 0,
                "avg_processing_time_ms": 0.0,
                "last_event_time": None
            }
        
        self.handlers[event_type].append(handler)
        
        # Add handler metadata
        if hasattr(handler, '__name__'):
            handler_name = handler.__name__
        else:
            handler_name = f"handler_{len(self.handlers[event_type])}"
        
        if not hasattr(handler, '_mcp_handler_id'):
            handler._mcp_handler_id = handler_id or handler_name
        
        logger.debug(f"Registered handler {handler_name} for event type {event_type}")
    
    def unregister_handler(self, event_type: str, handler: AsyncEventHandler):
        """Unregister an event handler."""
        if event_type in self.handlers:
            try:
                self.handlers[event_type].remove(handler)
                if not self.handlers[event_type]:
                    del self.handlers[event_type]
                    del self.handler_stats[event_type]
                logger.debug(f"Unregistered handler for event type {event_type}")
            except ValueError:
                pass
    
    def add_error_handler(self, error_handler: Callable[[Exception, Event], None]):
        """Add a global error handler for event processing failures."""
        self.error_handlers.append(error_handler)
    
    async def handle_event(self, event: Event):
        """Handle an event by dispatching it to registered handlers."""
        event_type = type(event).__name__
        
        if event_type not in self.handlers:
            logger.debug(f"No handlers registered for event type {event_type}")
            return
        
        # Update stats
        stats = self.handler_stats[event_type]
        stats["total_events"] += 1
        stats["last_event_time"] = datetime.now().isoformat()
        
        # Process handlers
        start_time = datetime.now()
        successful_handlers = 0
        failed_handlers = 0
        
        for handler in self.handlers[event_type]:
            try:
                await handler(event)
                successful_handlers += 1
                
            except Exception as e:
                failed_handlers += 1
                logger.error(f"Error in event handler {getattr(handler, '_mcp_handler_id', 'unknown')}: {e}")
                
                # Call error handlers
                for error_handler in self.error_handlers:
                    try:
                        error_handler(e, event)
                    except Exception as eh_error:
                        logger.error(f"Error in error handler: {eh_error}")
        
        # Update stats
        end_time = datetime.now()
        processing_time_ms = (end_time - start_time).total_seconds() * 1000
        
        stats["successful_events"] += successful_handlers
        stats["failed_events"] += failed_handlers
        
        # Update average processing time
        if stats["total_events"] > 0:
            current_avg = stats["avg_processing_time_ms"]
            new_avg = ((current_avg * (stats["total_events"] - 1)) + processing_time_ms) / stats["total_events"]
            stats["avg_processing_time_ms"] = new_avg
    
    def get_stats(self) -> Dict[str, Any]:
        """Get handler statistics."""
        return {
            "handler_stats": self.handler_stats.copy(),
            "total_handlers": sum(len(handlers) for handlers in self.handlers.values()),
            "event_types": list(self.handlers.keys())
        }


class MCPToolExecutionTracker:
    """
    Tracks MCP tool execution lifecycle and provides monitoring capabilities.
    
    This tracker provides:
    - Execution state management
    - Performance metrics collection
    - Timeout and failure detection
    - Execution history and analytics
    """
    
    def __init__(self, cleanup_interval_minutes: int = 60):
        self.active_executions: Dict[str, Dict[str, Any]] = {}
        self.completed_executions: List[Dict[str, Any]] = []
        self.execution_metrics: Dict[str, Any] = {
            "total_executions": 0,
            "successful_executions": 0,
            "failed_executions": 0,
            "avg_execution_time_ms": 0.0,
            "longest_execution_ms": 0.0,
            "shortest_execution_ms": float('inf')
        }
        
        # Cleanup configuration
        self.cleanup_interval = timedelta(minutes=cleanup_interval_minutes)
        self.max_completed_history = 1000
        
        # Start cleanup task
        self._cleanup_task = asyncio.create_task(self._periodic_cleanup())
    
    async def start_execution(self, event: MCPToolExecutionStartedEvent):
        """Track the start of a tool execution."""
        execution_info = {
            "execution_id": event.execution_id,
            "mcp_name": event.mcp_name,
            "tool_name": event.tool_name,
            "arguments": event.tool_arguments,
            "start_time": datetime.fromisoformat(event.start_time),
            "status": "running",
            "session_id": event.session_id
        }
        
        self.active_executions[event.execution_id] = execution_info
        logger.debug(f"Started tracking execution {event.execution_id} for tool {event.tool_name}")
    
    async def complete_execution(self, event: MCPToolExecutionCompletedEvent):
        """Track the completion of a tool execution."""
        execution_id = event.execution_id
        
        if execution_id not in self.active_executions:
            logger.warning(f"Completion event for unknown execution {execution_id}")
            return
        
        execution_info = self.active_executions.pop(execution_id)
        
        # Calculate execution time
        end_time = datetime.fromisoformat(event.end_time)
        start_time = execution_info["start_time"]
        execution_time_ms = (end_time - start_time).total_seconds() * 1000
        
        # Update execution info
        execution_info.update({
            "end_time": end_time,
            "execution_time_ms": execution_time_ms,
            "success": event.success,
            "result": event.tool_result,
            "error_message": event.error_message,
            "status": "completed"
        })
        
        # Add to completed executions
        self.completed_executions.append(execution_info)
        
        # Update metrics
        self._update_metrics(execution_info)
        
        logger.debug(f"Completed tracking execution {execution_id} (success: {event.success})")
    
    def _update_metrics(self, execution_info: Dict[str, Any]):
        """Update execution metrics."""
        metrics = self.execution_metrics
        execution_time_ms = execution_info["execution_time_ms"]
        
        metrics["total_executions"] += 1
        
        if execution_info["success"]:
            metrics["successful_executions"] += 1
        else:
            metrics["failed_executions"] += 1
        
        # Update timing metrics
        if execution_time_ms > metrics["longest_execution_ms"]:
            metrics["longest_execution_ms"] = execution_time_ms
        
        if execution_time_ms < metrics["shortest_execution_ms"]:
            metrics["shortest_execution_ms"] = execution_time_ms
        
        # Update average execution time
        total_executions = metrics["total_executions"]
        current_avg = metrics["avg_execution_time_ms"]
        new_avg = ((current_avg * (total_executions - 1)) + execution_time_ms) / total_executions
        metrics["avg_execution_time_ms"] = new_avg
    
    def get_execution_status(self, execution_id: str) -> Optional[Dict[str, Any]]:
        """Get the status of a specific execution."""
        if execution_id in self.active_executions:
            return self.active_executions[execution_id].copy()
        
        # Check completed executions
        for execution in self.completed_executions:
            if execution["execution_id"] == execution_id:
                return execution.copy()
        
        return None
    
    def get_active_executions(self) -> Dict[str, Dict[str, Any]]:
        """Get all active executions."""
        return self.active_executions.copy()
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get execution metrics."""
        return {
            **self.execution_metrics.copy(),
            "active_executions": len(self.active_executions),
            "completed_executions": len(self.completed_executions)
        }
    
    def get_execution_history(
        self,
        tool_name: Optional[str] = None,
        mcp_name: Optional[str] = None,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Get execution history with optional filtering."""
        executions = self.completed_executions
        
        # Apply filters
        if tool_name:
            executions = [e for e in executions if e["tool_name"] == tool_name]
        
        if mcp_name:
            executions = [e for e in executions if e["mcp_name"] == mcp_name]
        
        # Sort by end time (most recent first)
        executions.sort(key=lambda e: e["end_time"], reverse=True)
        
        # Apply limit
        if limit:
            executions = executions[:limit]
        
        return executions
    
    async def _periodic_cleanup(self):
        """Periodically clean up old completed executions."""
        while True:
            try:
                await asyncio.sleep(self.cleanup_interval.total_seconds())
                
                # Remove old completed executions
                if len(self.completed_executions) > self.max_completed_history:
                    # Keep only the most recent executions
                    self.completed_executions.sort(key=lambda e: e["end_time"], reverse=True)
                    self.completed_executions = self.completed_executions[:self.max_completed_history]
                    logger.debug(f"Cleaned up execution history, kept {self.max_completed_history} entries")
                
                # Check for stuck executions (running for more than 1 hour)
                current_time = datetime.now()
                stuck_threshold = timedelta(hours=1)
                
                stuck_executions = []
                for execution_id, execution_info in self.active_executions.items():
                    if current_time - execution_info["start_time"] > stuck_threshold:
                        stuck_executions.append(execution_id)
                
                # Log stuck executions
                for execution_id in stuck_executions:
                    execution_info = self.active_executions[execution_id]
                    logger.warning(
                        f"Execution {execution_id} for tool {execution_info['tool_name']} "
                        f"has been running for over 1 hour"
                    )
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in periodic cleanup: {e}")
    
    async def cleanup(self):
        """Clean up tracker resources."""
        if self._cleanup_task and not self._cleanup_task.done():
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass


class MCPEventHandlers:
    """
    Collection of pre-built event handlers for common MCP integration scenarios.
    
    This class provides ready-to-use event handlers that can be easily
    registered with the message bridge or event registry.
    """
    
    def __init__(self, tracker: Optional[MCPToolExecutionTracker] = None):
        self.tracker = tracker or MCPToolExecutionTracker()
        self.tool_registry: Dict[str, Dict[str, Any]] = {}
    
    async def handle_tool_registered(self, event: MCPToolRegisteredEvent):
        """Handle tool registration events."""
        tool_key = f"{event.mcp_name}:{event.tool_name}"
        self.tool_registry[tool_key] = {
            "mcp_name": event.mcp_name,
            "tool_name": event.tool_name,
            "schema": event.tool_schema,
            "registration_time": event.registration_time,
            "session_id": event.session_id
        }
        
        logger.info(f"Registered MCP tool: {tool_key}")
    
    async def handle_execution_started(self, event: MCPToolExecutionStartedEvent):
        """Handle tool execution start events."""
        await self.tracker.start_execution(event)
        
        logger.info(
            f"Started execution {event.execution_id} for tool "
            f"{event.mcp_name}:{event.tool_name}"
        )
    
    async def handle_execution_completed(self, event: MCPToolExecutionCompletedEvent):
        """Handle tool execution completion events."""
        await self.tracker.complete_execution(event)
        
        status = "succeeded" if event.success else "failed"
        logger.info(
            f"Completed execution {event.execution_id} for tool "
            f"{event.mcp_name}:{event.tool_name} - {status}"
        )
        
        if not event.success and event.error_message:
            logger.error(f"Execution error: {event.error_message}")
    
    async def handle_server_connection(self, event: MCPServerConnectionEvent):
        """Handle MCP server connection events."""
        logger.info(
            f"MCP server {event.mcp_name} connection status: {event.connection_status}"
        )
        
        if event.connection_status == "disconnected":
            # Remove tools from registry for disconnected server
            tools_to_remove = [
                key for key in self.tool_registry.keys()
                if key.startswith(f"{event.mcp_name}:")
            ]
            
            for tool_key in tools_to_remove:
                del self.tool_registry[tool_key]
                logger.debug(f"Removed tool {tool_key} due to server disconnection")
    
    def get_registered_tools(self) -> Dict[str, Dict[str, Any]]:
        """Get all registered tools."""
        return self.tool_registry.copy()
    
    def get_execution_metrics(self) -> Dict[str, Any]:
        """Get execution metrics from the tracker."""
        return self.tracker.get_metrics()
    
    async def cleanup(self):
        """Clean up handler resources."""
        await self.tracker.cleanup()


# ==================== Utility Functions ====================

def create_default_event_handlers() -> MCPEventHandlers:
    """Create a default set of MCP event handlers."""
    return MCPEventHandlers()


def setup_event_registry_with_defaults() -> MCPEventHandlerRegistry:
    """Set up an event registry with default MCP event handlers."""
    registry = MCPEventHandlerRegistry()
    handlers = create_default_event_handlers()
    
    # Register default handlers
    registry.register_handler("MCPToolRegisteredEvent", handlers.handle_tool_registered)
    registry.register_handler("MCPToolExecutionStartedEvent", handlers.handle_execution_started)
    registry.register_handler("MCPToolExecutionCompletedEvent", handlers.handle_execution_completed)
    registry.register_handler("MCPServerConnectionEvent", handlers.handle_server_connection)
    
    return registry


def create_logging_error_handler() -> Callable[[Exception, Event], None]:
    """Create an error handler that logs exceptions."""
    def log_error(exception: Exception, event: Event):
        event_type = type(event).__name__
        logger.error(f"Event handler error for {event_type}: {exception}")
        
        # Log additional context if available
        if hasattr(event, 'mcp_name'):
            logger.error(f"MCP Name: {event.mcp_name}")
        if hasattr(event, 'tool_name'):
            logger.error(f"Tool Name: {event.tool_name}")
        if hasattr(event, 'execution_id'):
            logger.error(f"Execution ID: {event.execution_id}")
    
    return log_error
