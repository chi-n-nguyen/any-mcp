import asyncio
import logging
import time
from typing import Any, Callable, Optional, TypeVar, Union
from functools import wraps
from enum import Enum

logger = logging.getLogger(__name__)

T = TypeVar('T')


class MCPErrorType(Enum):
    CONNECTION_ERROR = "connection_error"
    TIMEOUT_ERROR = "timeout_error"
    TOOL_NOT_FOUND = "tool_not_found"
    INVALID_ARGUMENTS = "invalid_arguments"
    AUTHENTICATION_ERROR = "authentication_error"
    RATE_LIMIT_ERROR = "rate_limit_error"
    SERVER_ERROR = "server_error"
    UNKNOWN_ERROR = "unknown_error"


class MCPError(Exception):
    """Base exception for MCP-related errors."""
    
    def __init__(self, message: str, error_type: MCPErrorType = MCPErrorType.UNKNOWN_ERROR, 
                 mcp_name: str = None, tool_name: str = None, original_error: Exception = None):
        super().__init__(message)
        self.error_type = error_type
        self.mcp_name = mcp_name
        self.tool_name = tool_name
        self.original_error = original_error
        self.timestamp = time.time()


class MCPConnectionError(MCPError):
    """Raised when unable to connect to an MCP server."""
    
    def __init__(self, message: str, mcp_name: str = None, original_error: Exception = None):
        super().__init__(message, MCPErrorType.CONNECTION_ERROR, mcp_name, original_error=original_error)


class MCPTimeoutError(MCPError):
    """Raised when an MCP operation times out."""
    
    def __init__(self, message: str, mcp_name: str = None, tool_name: str = None, timeout: float = None):
        super().__init__(message, MCPErrorType.TIMEOUT_ERROR, mcp_name, tool_name)
        self.timeout = timeout


class MCPToolNotFoundError(MCPError):
    """Raised when a requested tool is not found."""
    
    def __init__(self, tool_name: str, mcp_name: str = None, available_tools: list = None):
        message = f"Tool '{tool_name}' not found"
        if mcp_name:
            message += f" in MCP '{mcp_name}'"
        if available_tools:
            message += f". Available tools: {', '.join(available_tools)}"
        
        super().__init__(message, MCPErrorType.TOOL_NOT_FOUND, mcp_name, tool_name)
        self.available_tools = available_tools or []


class MCPAuthenticationError(MCPError):
    """Raised when authentication fails."""
    
    def __init__(self, message: str, mcp_name: str = None):
        super().__init__(message, MCPErrorType.AUTHENTICATION_ERROR, mcp_name)


class MCPRateLimitError(MCPError):
    """Raised when rate limits are exceeded."""
    
    def __init__(self, message: str, mcp_name: str = None, retry_after: int = None):
        super().__init__(message, MCPErrorType.RATE_LIMIT_ERROR, mcp_name)
        self.retry_after = retry_after


def with_timeout(timeout_seconds: float):
    """Decorator to add timeout to async functions."""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                return await asyncio.wait_for(func(*args, **kwargs), timeout=timeout_seconds)
            except asyncio.TimeoutError:
                raise MCPTimeoutError(
                    f"Operation timed out after {timeout_seconds} seconds",
                    timeout=timeout_seconds
                )
        return wrapper
    return decorator


def with_retry(max_attempts: int = 3, delay: float = 1.0, backoff_factor: float = 2.0):
    """Decorator to add retry logic to functions."""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            last_exception = None
            current_delay = delay
            
            for attempt in range(max_attempts):
                try:
                    return await func(*args, **kwargs)
                except (MCPConnectionError, MCPTimeoutError, MCPRateLimitError) as e:
                    last_exception = e
                    
                    if attempt == max_attempts - 1:  # Last attempt
                        break
                    
                    # Handle rate limiting specially
                    if isinstance(e, MCPRateLimitError) and e.retry_after:
                        wait_time = e.retry_after
                    else:
                        wait_time = current_delay
                    
                    logger.warning(f"Attempt {attempt + 1} failed: {e}. Retrying in {wait_time}s...")
                    await asyncio.sleep(wait_time)
                    current_delay *= backoff_factor
                    
                except Exception as e:
                    # Don't retry on other types of errors
                    raise
            
            # If we get here, all attempts failed
            raise last_exception
        return wrapper
    return decorator


def handle_mcp_errors(mcp_name: str = None):
    """Decorator to convert generic exceptions to MCP-specific exceptions."""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except MCPError:
                # Already an MCP error, re-raise as-is
                raise
            except ConnectionError as e:
                raise MCPConnectionError(
                    f"Failed to connect to MCP server: {str(e)}",
                    mcp_name=mcp_name,
                    original_error=e
                )
            except asyncio.TimeoutError as e:
                raise MCPTimeoutError(
                    f"MCP operation timed out: {str(e)}",
                    mcp_name=mcp_name
                )
            except PermissionError as e:
                raise MCPAuthenticationError(
                    f"Authentication failed: {str(e)}",
                    mcp_name=mcp_name
                )
            except Exception as e:
                # Generic exception handling
                raise MCPError(
                    f"Unexpected error in MCP operation: {str(e)}",
                    error_type=MCPErrorType.SERVER_ERROR,
                    mcp_name=mcp_name,
                    original_error=e
                )
        return wrapper
    return decorator


class CircuitBreaker:
    """Circuit breaker pattern for MCP operations."""
    
    def __init__(self, failure_threshold: int = 5, recovery_timeout: float = 60.0, 
                 expected_exception: type = MCPError):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception
        
        self.failure_count = 0
        self.last_failure_time = None
        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN
    
    def __call__(self, func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            if self.state == "OPEN":
                if time.time() - self.last_failure_time > self.recovery_timeout:
                    self.state = "HALF_OPEN"
                    logger.info("Circuit breaker moving to HALF_OPEN state")
                else:
                    raise MCPError("Circuit breaker is OPEN - too many failures")
            
            try:
                result = await func(*args, **kwargs)
                # Success - reset failure count
                if self.state == "HALF_OPEN":
                    self.state = "CLOSED"
                    logger.info("Circuit breaker moving to CLOSED state")
                self.failure_count = 0
                return result
                
            except self.expected_exception as e:
                self.failure_count += 1
                self.last_failure_time = time.time()
                
                if self.failure_count >= self.failure_threshold:
                    self.state = "OPEN"
                    logger.warning(f"Circuit breaker moving to OPEN state after {self.failure_count} failures")
                
                raise
                
        return wrapper


async def safe_call_with_fallback(primary_func: Callable, fallback_func: Callable = None, 
                                 *args, **kwargs) -> Any:
    """
    Safely call a function with optional fallback.
    
    Args:
        primary_func: Primary function to call
        fallback_func: Optional fallback function if primary fails
        *args, **kwargs: Arguments to pass to functions
        
    Returns:
        Result from primary function or fallback
    """
    try:
        return await primary_func(*args, **kwargs)
    except Exception as e:
        logger.warning(f"Primary function failed: {e}")
        
        if fallback_func:
            try:
                logger.info("Attempting fallback function")
                return await fallback_func(*args, **kwargs)
            except Exception as fallback_e:
                logger.error(f"Fallback function also failed: {fallback_e}")
                raise e  # Raise original exception
        else:
            raise


class ErrorAggregator:
    """Collect and analyze MCP errors for monitoring."""
    
    def __init__(self, max_errors: int = 1000):
        self.max_errors = max_errors
        self.errors = []
    
    def add_error(self, error: MCPError):
        """Add an error to the aggregator."""
        self.errors.append(error)
        
        # Keep only recent errors
        if len(self.errors) > self.max_errors:
            self.errors = self.errors[-self.max_errors:]
    
    def get_error_stats(self, time_window: float = 3600) -> dict:
        """Get error statistics for a time window (default: 1 hour)."""
        current_time = time.time()
        recent_errors = [
            error for error in self.errors 
            if current_time - error.timestamp <= time_window
        ]
        
        if not recent_errors:
            return {"total_errors": 0}
        
        # Count by error type
        error_types = {}
        mcp_errors = {}
        tool_errors = {}
        
        for error in recent_errors:
            # By error type
            error_type = error.error_type.value
            error_types[error_type] = error_types.get(error_type, 0) + 1
            
            # By MCP
            if error.mcp_name:
                mcp_errors[error.mcp_name] = mcp_errors.get(error.mcp_name, 0) + 1
            
            # By tool
            if error.tool_name:
                tool_errors[error.tool_name] = tool_errors.get(error.tool_name, 0) + 1
        
        return {
            "total_errors": len(recent_errors),
            "time_window_hours": time_window / 3600,
            "by_error_type": error_types,
            "by_mcp": mcp_errors,
            "by_tool": tool_errors,
            "most_recent_error": recent_errors[-1].timestamp if recent_errors else None
        }


# Global error aggregator instance
error_aggregator = ErrorAggregator() 