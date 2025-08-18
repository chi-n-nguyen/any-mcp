"""
Tool Adapter for llmgine Integration

This module provides conversion between MCP tools and llmgine tools,
enabling seamless tool registration and execution across both systems.
"""

import logging
from typing import Dict, Any, Optional, List
from mcp.types import Tool as MCPTool, CallToolResult

# llmgine imports (will be optional)
try:
    from llmgine.llm.tools.tool import Tool as LLMgineTool
    from llmgine.llm.tools.tool import Parameter
    LLMGINE_AVAILABLE = True
except ImportError:
    LLMGINE_AVAILABLE = False
    # Mock classes for when llmgine is not available
    class LLMgineTool:
        pass
    class Parameter:
        pass

# any-mcp imports
from any_mcp.managers.manager import MCPManager

logger = logging.getLogger(__name__)


class LLMgineToolAdapter:
    """
    Adapter for converting between MCP tools and llmgine tools.
    
    This adapter handles:
    - Converting MCP tool schemas to llmgine tool parameters
    - Converting MCP tool results to llmgine tool results
    - Maintaining compatibility between both tool systems
    """
    
    def __init__(self, mcp_manager: MCPManager):
        self.mcp_manager = mcp_manager
        
    def convert_mcp_tool(self, mcp_tool: MCPTool, mcp_name: str) -> Optional[LLMgineTool]:
        """
        Convert an MCP tool to a llmgine tool.
        
        Args:
            mcp_tool: The MCP tool to convert
            mcp_name: Name of the MCP server
            
        Returns:
            LLMgineTool instance or None if conversion fails
        """
        if not LLMGINE_AVAILABLE:
            logger.warning("llmgine not available, cannot convert MCP tool")
            return None
            
        try:
            # Extract tool information
            tool_name = mcp_tool.name
            description = mcp_tool.description or f"Tool {tool_name} from {mcp_name}"
            
            # Convert input schema to llmgine parameters
            parameters = self._convert_input_schema(mcp_tool.inputSchema)
            
            # Create llmgine tool
            llmgine_tool = LLMgineTool(
                name=f"{mcp_name}:{tool_name}",
                description=description,
                parameters=parameters,
                execute=self._create_tool_executor(mcp_name, tool_name)
            )
            
            logger.debug(f"Converted MCP tool {tool_name} to llmgine tool")
            return llmgine_tool
            
        except Exception as e:
            logger.error(f"Failed to convert MCP tool {mcp_tool.name}: {e}")
            return None
    
    def _convert_input_schema(self, input_schema: Dict[str, Any]) -> List[Parameter]:
        """
        Convert MCP input schema to llmgine parameters.
        
        Args:
            input_schema: MCP tool input schema
            
        Returns:
            List of llmgine Parameter objects
        """
        if not input_schema or not isinstance(input_schema, dict):
            return []
        
        parameters = []
        properties = input_schema.get('properties', {})
        required = input_schema.get('required', [])
        
        for param_name, param_info in properties.items():
            try:
                # Extract parameter information
                param_type = self._convert_mcp_type_to_python(param_info.get('type', 'string'))
                param_description = param_info.get('description', f'Parameter {param_name}')
                param_required = param_name in required
                param_default = param_info.get('default')
                
                # Create llmgine parameter
                parameter = Parameter(
                    name=param_name,
                    type=param_type,
                    description=param_description,
                    required=param_required
                )
                
                # Set default value if provided
                if param_default is not None:
                    parameter.default = param_default
                
                parameters.append(parameter)
                
            except Exception as e:
                logger.warning(f"Failed to convert parameter {param_name}: {e}")
                continue
        
        return parameters
    
    def _convert_mcp_type_to_python(self, mcp_type: str) -> type:
        """
        Convert MCP JSON schema types to Python types.
        
        Args:
            mcp_type: MCP JSON schema type
            
        Returns:
            Python type
        """
        type_mapping = {
            'string': str,
            'number': float,
            'integer': int,
            'boolean': bool,
            'array': list,
            'object': dict
        }
        
        return type_mapping.get(mcp_type, str)
    
    def _create_tool_executor(self, mcp_name: str, tool_name: str):
        """
        Create a tool executor function for the llmgine tool.
        
        Args:
            mcp_name: Name of the MCP server
            tool_name: Name of the tool
            
        Returns:
            Async function that executes the tool
        """
        async def tool_executor(**kwargs):
            """Execute the MCP tool with the given arguments."""
            try:
                # Execute tool through MCP manager
                result = await self.mcp_manager.call_mcp(mcp_name, tool_name, kwargs)
                
                if result:
                    # Convert result to appropriate format
                    return self._format_tool_result(result)
                else:
                    raise RuntimeError(f"Tool {tool_name} execution failed")
                    
            except Exception as e:
                logger.error(f"Error executing tool {tool_name}: {e}")
                raise
        
        return tool_executor
    
    def _format_tool_result(self, result: CallToolResult) -> Any:
        """
        Format MCP tool result for llmgine consumption.
        
        Args:
            result: MCP tool result
            
        Returns:
            Formatted result
        """
        try:
            if result.content and len(result.content) > 0:
                content = result.content[0]
                
                # Extract text content if available
                if hasattr(content, 'text'):
                    return content.text
                
                # Extract other content types
                if hasattr(content, 'type'):
                    if content.type == 'text':
                        return content.text
                    elif content.type == 'image':
                        return f"Image: {content.uri}"
                    elif content.type == 'code':
                        return f"Code ({content.language}): {content.code}"
                
                # Fallback to string representation
                return str(content)
            
            return "No result content"
            
        except Exception as e:
            logger.warning(f"Failed to format tool result: {e}")
            return str(result)
    
    def convert_tool_result(self, result: CallToolResult, mcp_name: str, tool_name: str) -> Dict[str, Any]:
        """
        Convert MCP tool result to llmgine tool result format.
        
        Args:
            result: MCP tool result
            mcp_name: Name of the MCP server
            tool_name: Name of the tool
            
        Returns:
            Formatted tool result
        """
        try:
            formatted_result = self._format_tool_result(result)
            
            return {
                "mcp_name": mcp_name,
                "tool_name": tool_name,
                "result": formatted_result,
                "success": True,
                "timestamp": getattr(result, 'timestamp', None)
            }
            
        except Exception as e:
            logger.error(f"Failed to convert tool result: {e}")
            return {
                "mcp_name": mcp_name,
                "tool_name": tool_name,
                "result": f"Error: {str(e)}",
                "success": False,
                "timestamp": None
            }
    
    def get_tool_metadata(self, mcp_name: str, tool_name: str) -> Dict[str, Any]:
        """
        Get metadata about a specific tool.
        
        Args:
            mcp_name: Name of the MCP server
            tool_name: Name of the tool
            
        Returns:
            Tool metadata dictionary
        """
        try:
            client = self.mcp_manager.active_clients.get(mcp_name)
            if not client:
                return {}
            
            # This would need to be implemented based on MCP server capabilities
            # For now, return basic metadata
            return {
                "mcp_name": mcp_name,
                "tool_name": tool_name,
                "available": True,
                "client_type": type(client).__name__
            }
            
        except Exception as e:
            logger.error(f"Failed to get tool metadata: {e}")
            return {}
    
    def list_available_tools(self) -> List[Dict[str, Any]]:
        """
        List all available tools with their metadata.
        
        Returns:
            List of tool metadata dictionaries
        """
        tools = []
        
        try:
            for mcp_name, client in self.mcp_manager.active_clients.items():
                try:
                    # Get tools from client
                    client_tools = asyncio.run(client.list_tools())
                    
                    for tool in client_tools:
                        tool_info = {
                            "mcp_name": mcp_name,
                            "tool_name": tool.name,
                            "description": tool.description,
                            "input_schema": tool.inputSchema,
                            "available": True
                        }
                        tools.append(tool_info)
                        
                except Exception as e:
                    logger.warning(f"Failed to get tools from MCP {mcp_name}: {e}")
                    continue
                    
        except Exception as e:
            logger.error(f"Failed to list available tools: {e}")
        
        return tools
