# any-mcp

A universal adapter that safely starts any MCP package, discovers available tools, and provides a unified interface for users and LLMs to interact with them through a single, standardized API.

## Mission

Build **one adapter layer** that lets LLMs plug-and-play with *any* third-party MCP found on the internet—no bespoke coding required each time.

## Key Features

- **Universal Adapter**: One interface for all MCPs regardless of underlying implementation
- **Auto-Discovery**: Automatically detect and catalog available tools from any MCP
- **Multi-Source Installation**: Install MCPs from Docker, local files, or registry
- **Web API**: RESTful interface for remote MCP management and tool calling
- **Robust Error Handling**: Comprehensive error handling with retries and circuit breakers
- **Health Monitoring**: Real-time health checks and status monitoring
- **Production Ready**: Includes configuration management, logging, and cleanup

## Architecture

### Core Components

1. **MCP Installer** - Install and manage MCP packages from multiple sources
2. **MCP Manager** - Lifecycle management, health monitoring, and tool orchestration
3. **MCP Client** - Enhanced client with full tool discovery and calling capabilities
4. **Web API** - FastAPI-based HTTP interface for all MCP operations
5. **Error Handling** - Comprehensive error handling with circuit breakers and retries
6. **Configuration System** - YAML-based configuration with environment variable support

## Quick Start

### Installation

```bash
# Install dependencies
pip install -e .

# Copy example configuration
cp example_mcp_config.yaml mcp_config.yaml

# Set environment variables (optional)
export GITHUB_TOKEN=your_github_token_here
export USE_UV=1  # Use uv for faster Python execution
```

### Basic Usage

#### 1. Command Line Interface

```bash
# Run the enhanced CLI with multiple MCPs
python main.py

# Or run with specific MCP servers
python main.py demos/mcp_calc_server.py
```

#### 2. Web API Server

```bash
# Start the web API server
python -m api.web_mcp

# Or use uvicorn directly
uvicorn api.web_mcp:app --host 0.0.0.0 --port 8000 --reload
```

#### 3. Programmatic Usage

```python
from mcp_manager import MCPManager
from mcp_installer import MCPInstaller

# Install an MCP
installer = MCPInstaller()
installer.install_mcp(
    name="github",
    source="docker://ghcr.io/github/github-mcp-server",
    env_vars={"GITHUB_TOKEN": "your_token"}
)

# Use the MCP
async with MCPManager() as manager:
    # List available tools
    tools = await manager.list_mcp_tools("github")
    
    # Call a tool
    result = await manager.call_mcp(
        "github", 
        "search_repositories", 
        {"query": "mcp language:python"}
    )
```

### Web API Examples

```bash
# List all MCPs
curl http://localhost:8000/mcp

# Install a new MCP
curl -X POST http://localhost:8000/mcp/install \
  -H "Content-Type: application/json" \
  -d '{
    "name": "calculator",
    "source": "local://./demos/mcp_calc_server.py",
    "description": "Calculator MCP for math operations"
  }'

# Call a tool
curl -X POST http://localhost:8000/mcp/calculator/call \
  -H "Content-Type: application/json" \
  -d '{
    "tool_name": "add",
    "args": {"a": 5, "b": 3}
  }'

# Check MCP health
curl http://localhost:8000/mcp/calculator/health
```

## Configuration

Create a `mcp_config.yaml` file to define your MCPs:

```yaml
installed_mcps:
  github:
    type: "docker"
    source: "ghcr.io/github/github-mcp-server"
    description: "GitHub's official MCP server"
    env_vars:
      GITHUB_PERSONAL_ACCESS_TOKEN: "${GITHUB_TOKEN}"
    enabled: true

  calculator:
    type: "local"
    source: "./demos/mcp_calc_server.py"
    description: "Mathematical operations"
    enabled: true
```

## Supported MCP Sources

### Docker MCPs
```bash
# Install from Docker registry
installer.install_mcp(
    "github",
    "docker://ghcr.io/github/github-mcp-server"
)
```

### Local MCPs
```bash
# Install from local file
installer.install_mcp(
    "calculator",
    "local://./demos/mcp_calc_server.py"
)
```

### Registry MCPs (Future)
```bash
# Install from MCP registry (planned)
installer.install_mcp(
    "financial",
    "registry://financial-data-mcp"
)
```

## Demo Scripts

Run the included demonstrations:

```bash
# Simple conceptual demo
python demos/simple_demo.py

# Real GitHub MCP integration
python demos/real_github_demo.py

# Calculator MCP demo
python demos/calc_demo.py

# Basic GitHub MCP demo
python demos/github_mcp_demo.py
```

## Error Handling and Resilience

The system includes comprehensive error handling:

- **Custom Exception Types**: Specific exceptions for different error scenarios
- **Retry Logic**: Automatic retries with exponential backoff
- **Circuit Breakers**: Prevent cascading failures
- **Timeout Protection**: Configurable timeouts for all operations
- **Error Aggregation**: Collect and analyze errors for monitoring

## API Documentation

When running the web API, visit:
- **API Docs**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/health

## Development

### Project Structure

```
mcp/
├── api/                    # Web API implementation
│   ├── web_mcp.py         # FastAPI application
│   └── __init__.py
├── core/                   # Core functionality
│   ├── chat.py            # Chat interface
│   ├── claude.py          # Claude integration
│   ├── cli_chat.py        # CLI chat implementation
│   ├── cli.py             # Command line interface
│   ├── tools.py           # Tool management
│   └── error_handling.py  # Error handling system
├── demos/                  # Example MCPs and demos
│   ├── calc_demo.py       # Calculator demo
│   ├── github_mcp_demo.py # GitHub MCP demo
│   ├── mcp_calc_server.py # Calculator MCP server
│   ├── real_github_demo.py # Real GitHub integration
│   └── simple_demo.py     # Basic demonstration
├── mcps/                   # Installed local MCPs
├── mcp_client.py          # Enhanced MCP client
├── mcp_installer.py       # MCP installation system
├── mcp_manager.py         # MCP lifecycle management
├── mcp_server.py          # Document MCP server
├── main.py                # Main application entry point
├── example_mcp_config.yaml # Example configuration
└── README.md              # This file
```

### Running Tests

```bash
# Install test dependencies
pip install pytest pytest-asyncio

# Run tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=. --cov-report=html
```

## Production Deployment

### Environment Variables

```bash
export CLAUDE_MODEL=claude-3-sonnet-20240229
export ANTHROPIC_API_KEY=your_anthropic_key
export GITHUB_TOKEN=your_github_token
export USE_UV=1
export LOG_LEVEL=INFO
```

### Docker Deployment

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY . .
RUN pip install -e .

EXPOSE 8000
CMD ["uvicorn", "api.web_mcp:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Health Monitoring

The system provides comprehensive health monitoring:

```bash
# Check overall system health
curl http://localhost:8000/health

# Check specific MCP health
curl http://localhost:8000/mcp/github/health

# Get detailed status of all MCPs
curl http://localhost:8000/mcp
```

## Development Timeline

### Week 1: Foundation
- **Core MCP Adapter**: Universal interface for any MCP package
- **Auto-Discovery**: Automatic tool detection and cataloging
- **Basic Demos**: GitHub, Calculator, and Document MCPs working
- **Simple CLI**: Command-line interface for MCP interaction

### Week 2: Production Infrastructure  
- **MCP Installer**: Multi-source installation (Docker, local, registry)
- **MCP Manager**: Lifecycle management and health monitoring
- **Web API**: FastAPI-based HTTP interface for all operations
- **Error Handling**: Retries, circuit breakers, comprehensive error management
- **Configuration**: YAML-based config with environment variable support

### Week 3 Goals
- **MCP Discovery Registry**: Searchable registry of available MCPs
- **Enhanced LLM Integration**: Direct integration with various LLM frameworks
- **Real-time WebSocket API**: Streaming tool execution results
- **Domain-specific MCPs**: Financial data, document processing, database MCPs

### Week 4 Goals
- **Production Dashboard**: Web-based monitoring and management interface
- **Advanced Authentication**: Role-based access control for MCPs
- **Performance Optimization**: Caching, connection pooling, load balancing
- **Enterprise Features**: Audit logging, compliance, enterprise integrations

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

For questions and support:
- Create an issue on GitHub
- Check the [API documentation](http://localhost:8000/docs) when running the server
- Review the example configurations and demos
