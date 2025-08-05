#!/usr/bin/env python3
"""
Week 2 Demo: Enhanced MCP System
Demonstrates the new installer, manager, web API, and error handling features.
"""

import asyncio
import logging
import sys
from pathlib import Path

# Add the project root to the path
sys.path.insert(0, str(Path(__file__).parent.parent))

from mcp_installer import MCPInstaller
from mcp_manager import MCPManager

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


async def demo_installer():
    """Demonstrate the MCP installer capabilities."""
    print("\n" + "="*60)
    print("WEEK 2 DEMO: MCP Installer System")
    print("="*60)
    
    installer = MCPInstaller()
    
    # Install local calculator MCP
    print("\n1. Installing Calculator MCP (local)")
    success = installer.install_mcp(
        name="calculator",
        source="local://./demos/mcp_calc_server.py",
        description="Calculator MCP for mathematical operations"
    )
    print(f"   Installation {'successful' if success else 'failed'}")
    
    # Install document MCP
    print("\n2. Installing Document MCP (local)")
    success = installer.install_mcp(
        name="documents",
        source="local://./mcp_server.py",
        description="Document management MCP"
    )
    print(f"   Installation {'successful' if success else 'failed'}")
    
    # Try to install GitHub MCP (will work if Docker is available)
    print("\n3. Installing GitHub MCP (Docker)")
    try:
        success = installer.install_mcp(
            name="github",
            source="docker://ghcr.io/github/github-mcp-server",
            description="GitHub's official MCP server",
            env_vars={"GITHUB_PERSONAL_ACCESS_TOKEN": "${GITHUB_TOKEN}"}
        )
        print(f"   Installation {'successful' if success else 'failed'}")
    except Exception as e:
        print(f"   Installation failed (expected without Docker): {e}")
    
    # List installed MCPs
    print("\n4. Listing Installed MCPs")
    installed = installer.list_installed_mcps()
    for mcp in installed:
        status = "enabled" if mcp.enabled else "disabled"
        print(f"   - {mcp.name} ({mcp.type.value}): {mcp.description} [{status}]")
    
    return installer


async def demo_manager(installer):
    """Demonstrate the MCP manager capabilities."""
    print("\n" + "="*60)
    print("WEEK 2 DEMO: MCP Manager System")
    print("="*60)
    
    async with MCPManager() as manager:
        # Show MCP status
        print("\n1. MCP Status Overview")
        status = await manager.get_mcp_status()
        for name, info in status.items():
            print(f"   - {name}: {info['type']} | "
                  f"Enabled: {info['enabled']} | "
                  f"Active: {info['active']} | "
                  f"Healthy: {info['healthy']}")
        
        # List all available tools
        print("\n2. Available Tools from All MCPs")
        all_tools = await manager.list_all_tools()
        for mcp_name, tools in all_tools.items():
            if tools:
                print(f"   {mcp_name} ({len(tools)} tools):")
                for tool in tools[:3]:  # Show first 3 tools
                    print(f"     - {tool.name}: {tool.description or 'No description'}")
                if len(tools) > 3:
                    print(f"     ... and {len(tools) - 3} more")
        
        # Demonstrate tool calling
        print("\n3. Tool Calling Demonstrations")
        
        # Try calculator operations
        if "calculator" in manager.active_clients:
            print("   Calculator Operations:")
            operations = [
                ("add", {"a": 15, "b": 25}),
                ("multiply", {"a": 7, "b": 8}),
                ("power", {"base": 2, "exponent": 10})
            ]
            
            for tool_name, args in operations:
                try:
                    result = await manager.call_mcp("calculator", tool_name, args)
                    if result and hasattr(result, 'content'):
                        print(f"     {tool_name}{args} = {result.content}")
                    else:
                        print(f"     {tool_name}{args} = {result}")
                except Exception as e:
                    print(f"     {tool_name}{args} failed: {e}")
        
        # Try document operations
        if "documents" in manager.active_clients:
            print("   Document Operations:")
            try:
                # List available documents
                tools = await manager.list_mcp_tools("documents")
                read_tool = next((t for t in tools if t.name == "read_document"), None)
                if read_tool:
                    result = await manager.call_mcp("documents", "read_document", {"doc_id": "plan.md"})
                    if result and hasattr(result, 'content'):
                        content = str(result.content)[:100] + "..." if len(str(result.content)) > 100 else str(result.content)
                        print(f"     Read plan.md: {content}")
            except Exception as e:
                print(f"     Document operation failed: {e}")
        
        # Health checks
        print("\n4. Health Check Results")
        for mcp_name in manager.active_clients:
            is_healthy = await manager.health_check(mcp_name)
            print(f"   {mcp_name}: {'Healthy' if is_healthy else 'Unhealthy'}")


async def demo_web_api_info():
    """Show information about the Web API capabilities."""
    print("\n" + "="*60)
    print("WEEK 2 DEMO: Web API Information")
    print("="*60)
    
    print("\nTo test the Web API, run in another terminal:")
    print("   python -m api.web_mcp")
    print("   # or")
    print("   uvicorn api.web_mcp:app --host 0.0.0.0 --port 8000 --reload")
    
    print("\nThen try these curl commands:")
    
    print("\n1. List all MCPs:")
    print("   curl http://localhost:8000/mcp")
    
    print("\n2. Install a new MCP:")
    print('   curl -X POST http://localhost:8000/mcp/install \\')
    print('     -H "Content-Type: application/json" \\')
    print('     -d \'{"name": "test", "source": "local://./demos/mcp_calc_server.py"}\'')
    
    print("\n3. List tools for an MCP:")
    print("   curl http://localhost:8000/mcp/calculator/tools")
    
    print("\n4. Call a tool:")
    print('   curl -X POST http://localhost:8000/mcp/calculator/call \\')
    print('     -H "Content-Type: application/json" \\')
    print('     -d \'{"tool_name": "add", "args": {"a": 10, "b": 5}}\'')
    
    print("\n5. Check MCP health:")
    print("   curl http://localhost:8000/mcp/calculator/health")
    
    print("\n6. View API documentation:")
    print("   Open browser to: http://localhost:8000/docs")


async def demo_error_handling():
    """Demonstrate error handling capabilities."""
    print("\n" + "="*60)
    print("WEEK 2 DEMO: Error Handling System")
    print("="*60)
    
    from core.error_handling import (
        MCPError, MCPConnectionError, MCPToolNotFoundError,
        with_timeout, with_retry, error_aggregator
    )
    
    print("\n1. Custom Exception Types")
    print("   - MCPError: Base exception for all MCP errors")
    print("   - MCPConnectionError: Connection failures")
    print("   - MCPToolNotFoundError: Tool not found")
    print("   - MCPTimeoutError: Operation timeouts")
    print("   - MCPAuthenticationError: Auth failures")
    print("   - MCPRateLimitError: Rate limiting")
    
    print("\n2. Error Handling Features")
    print("   - Automatic retries with exponential backoff")
    print("   - Circuit breaker pattern for failing services")
    print("   - Timeout protection for all operations")
    print("   - Error aggregation and monitoring")
    print("   - Graceful fallback mechanisms")
    
    # Show error aggregation
    print("\n3. Error Statistics (simulated)")
    # Simulate some errors for demonstration
    error_aggregator.add_error(MCPConnectionError("Connection failed", "test_mcp"))
    error_aggregator.add_error(MCPToolNotFoundError("unknown_tool", "test_mcp"))
    
    stats = error_aggregator.get_error_stats()
    print(f"   Total errors in last hour: {stats['total_errors']}")
    if stats['total_errors'] > 0:
        print(f"   By error type: {stats['by_error_type']}")
        print(f"   By MCP: {stats['by_mcp']}")


async def main():
    """Run the complete Week 2 demonstration."""
    print("any-mcp Week 2 Implementation Demo")
    print("Showcasing: Installer, Manager, Web API, Error Handling")
    print("="*60)
    
    try:
        # Demo 1: Installer
        installer = await demo_installer()
        
        # Demo 2: Manager
        await demo_manager(installer)
        
        # Demo 3: Web API Info
        await demo_web_api_info()
        
        # Demo 4: Error Handling
        await demo_error_handling()
        
        print("\n" + "="*60)
        print("Week 2 Demo Completed Successfully!")
        print("="*60)
        print("\nKey Achievements:")
        print("• MCP Installer: Install from Docker, local files, registry")
        print("• MCP Manager: Lifecycle management, health monitoring")
        print("• Enhanced MCP Client: Full tool discovery and calling")
        print("• Web API: RESTful interface for all operations")
        print("• Error Handling: Retries, circuit breakers, monitoring")
        print("• Configuration: YAML-based with environment variables")
        print("• Production Ready: Logging, cleanup, health checks")
        
        print("\nNext: Week 3 will add MCP registry, enhanced LLM integration,")
        print("and real-time capabilities!")
        
    except Exception as e:
        logger.error(f"Demo failed: {e}")
        print("\nDemo encountered an error. Check logs for details.")


if __name__ == "__main__":
    asyncio.run(main()) 