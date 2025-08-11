import asyncio
import logging
from typing import Dict, List, Any, Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from any_mcp.managers.manager import MCPManager
from any_mcp.managers.installer import MCPConfig

logger = logging.getLogger(__name__)

# Global MCP manager instance
mcp_manager: Optional[MCPManager] = None


class ToolCallRequest(BaseModel):
    tool_name: str
    args: Dict[str, Any]


class MCPInstallRequest(BaseModel):
    name: str
    source: str
    description: str = ""
    env_vars: Dict[str, str] = {}


class ToolInfo(BaseModel):
    name: str
    description: str = ""
    input_schema: Dict[str, Any] = {}


class MCPStatus(BaseModel):
    name: str
    type: str
    enabled: bool
    active: bool
    healthy: bool
    description: str


class APIResponse(BaseModel):
    success: bool
    data: Any = None
    error: str = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage MCP manager lifecycle."""
    global mcp_manager
    try:
        mcp_manager = MCPManager()
        await mcp_manager.initialize()
        logger.info("MCP manager initialized for web API")
        yield
    finally:
        if mcp_manager:
            await mcp_manager.cleanup()
            logger.info("MCP manager cleaned up")


# Create FastAPI app
app = FastAPI(
    title="MCP Web API",
    description="RESTful HTTP interface for managing and calling MCP tools",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "message": "MCP Web API is running"}


@app.get("/mcp", response_model=List[MCPStatus])
async def list_mcps():
    """List all installed MCPs with their status."""
    try:
        status_info = await mcp_manager.get_mcp_status()
        return [
            MCPStatus(
                name=name,
                type=info["type"],
                enabled=info["enabled"],
                active=info["active"],
                healthy=info["healthy"],
                description=info["description"]
            )
            for name, info in status_info.items()
        ]
    except Exception as e:
        logger.error(f"Failed to list MCPs: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list MCPs: {str(e)}"
        )


@app.post("/mcp/install", response_model=APIResponse)
async def install_mcp(request: MCPInstallRequest):
    """Install a new MCP."""
    try:
        success = mcp_manager.installer.install_mcp(
            name=request.name,
            source=request.source,
            description=request.description,
            env_vars=request.env_vars
        )
        
        if success:
            return APIResponse(success=True, data={"message": f"MCP {request.name} installed successfully"})
        else:
            return APIResponse(success=False, error=f"Failed to install MCP {request.name}")
            
    except Exception as e:
        logger.error(f"Failed to install MCP {request.name}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to install MCP: {str(e)}"
        )


@app.delete("/mcp/{mcp_name}", response_model=APIResponse)
async def uninstall_mcp(mcp_name: str):
    """Uninstall an MCP."""
    try:
        # Stop the MCP if it's running
        await mcp_manager.stop_mcp(mcp_name)
        
        # Uninstall it
        success = mcp_manager.installer.uninstall_mcp(mcp_name)
        
        if success:
            return APIResponse(success=True, data={"message": f"MCP {mcp_name} uninstalled successfully"})
        else:
            return APIResponse(success=False, error=f"Failed to uninstall MCP {mcp_name}")
            
    except Exception as e:
        logger.error(f"Failed to uninstall MCP {mcp_name}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to uninstall MCP: {str(e)}"
        )


@app.post("/mcp/{mcp_name}/start", response_model=APIResponse)
async def start_mcp(mcp_name: str):
    """Start an MCP."""
    try:
        success = await mcp_manager.setup_mcp(mcp_name)
        
        if success:
            return APIResponse(success=True, data={"message": f"MCP {mcp_name} started successfully"})
        else:
            return APIResponse(success=False, error=f"Failed to start MCP {mcp_name}")
            
    except Exception as e:
        logger.error(f"Failed to start MCP {mcp_name}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start MCP: {str(e)}"
        )


@app.post("/mcp/{mcp_name}/stop", response_model=APIResponse)
async def stop_mcp(mcp_name: str):
    """Stop an MCP."""
    try:
        success = await mcp_manager.stop_mcp(mcp_name)
        
        if success:
            return APIResponse(success=True, data={"message": f"MCP {mcp_name} stopped successfully"})
        else:
            return APIResponse(success=False, error=f"Failed to stop MCP {mcp_name}")
            
    except Exception as e:
        logger.error(f"Failed to stop MCP {mcp_name}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to stop MCP: {str(e)}"
        )


@app.post("/mcp/{mcp_name}/restart", response_model=APIResponse)
async def restart_mcp(mcp_name: str):
    """Restart an MCP."""
    try:
        success = await mcp_manager.restart_mcp(mcp_name)
        
        if success:
            return APIResponse(success=True, data={"message": f"MCP {mcp_name} restarted successfully"})
        else:
            return APIResponse(success=False, error=f"Failed to restart MCP {mcp_name}")
            
    except Exception as e:
        logger.error(f"Failed to restart MCP {mcp_name}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to restart MCP: {str(e)}"
        )


@app.get("/mcp/{mcp_name}/tools", response_model=List[ToolInfo])
async def list_mcp_tools(mcp_name: str):
    """List available tools for a specific MCP."""
    try:
        tools = await mcp_manager.list_mcp_tools(mcp_name)
        return [
            ToolInfo(
                name=tool.name,
                description=tool.description or "",
                input_schema=tool.inputSchema or {}
            )
            for tool in tools
        ]
    except Exception as e:
        logger.error(f"Failed to list tools for {mcp_name}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list tools: {str(e)}"
        )


@app.get("/mcp/tools", response_model=Dict[str, List[ToolInfo]])
async def list_all_tools():
    """List all available tools from all active MCPs."""
    try:
        all_tools = await mcp_manager.list_all_tools()
        result = {}
        
        for mcp_name, tools in all_tools.items():
            result[mcp_name] = [
                ToolInfo(
                    name=tool.name,
                    description=tool.description or "",
                    input_schema=tool.inputSchema or {}
                )
                for tool in tools
            ]
        
        return result
    except Exception as e:
        logger.error(f"Failed to list all tools: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list all tools: {str(e)}"
        )


@app.post("/mcp/{mcp_name}/call", response_model=APIResponse)
async def call_mcp_tool(mcp_name: str, request: ToolCallRequest):
    """Call a tool on a specific MCP."""
    try:
        result = await mcp_manager.call_mcp(mcp_name, request.tool_name, request.args)
        
        if result is not None:
            # Convert result to serializable format
            result_data = {
                "content": result.content if hasattr(result, 'content') else str(result),
                "isError": result.isError if hasattr(result, 'isError') else False
            }
            return APIResponse(success=True, data=result_data)
        else:
            return APIResponse(success=False, error=f"Tool call failed")
            
    except Exception as e:
        logger.error(f"Failed to call tool {request.tool_name} on {mcp_name}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to call tool: {str(e)}"
        )


@app.get("/mcp/{mcp_name}/health", response_model=APIResponse)
async def check_mcp_health(mcp_name: str):
    """Check health of a specific MCP."""
    try:
        is_healthy = await mcp_manager.health_check(mcp_name)
        return APIResponse(
            success=True, 
            data={"healthy": is_healthy, "message": f"MCP {mcp_name} is {'healthy' if is_healthy else 'unhealthy'}"}
        )
    except Exception as e:
        logger.error(f"Failed to check health for {mcp_name}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to check health: {str(e)}"
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api.web_mcp:app", host="0.0.0.0", port=8000, reload=True) 