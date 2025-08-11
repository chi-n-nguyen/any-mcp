# any-mcp

A universal adapter that safely starts any MCP package, discovers available tools, and provides a unified interface for users and LLMs to interact with them through a single, standardized API.

> **First Production Release v1.0.0** - Ready for LLMgine integration with full MCP protocol compliance, multi-LLM support, and production-ready deployment.

## Mission

Build **one adapter layer** that lets LLMs plug-and-play with *any* third-party MCP found on the internet—no bespoke coding required each time.

## Key Features

- **Natural Language Interface**: Talk to any MCP using plain English - no API knowledge needed
- **Universal Adapter**: One interface for all MCPs regardless of underlying implementation
- **Auto-Discovery**: Automatically detect and catalog available tools from any MCP
- **Multi-Source Installation**: Install MCPs from Docker, local files, or registry modules
- **Polished CLI**: Modern command-line interface with subcommands for all operations
- **Web API**: RESTful interface for remote MCP management and tool calling
- **Multi-LLM Support**: Optional LLM-powered chat mode with Claude and Gemini support for advanced natural language processing
- **Production Ready**: Includes configuration management, logging, and cleanup

## Architecture

```mermaid
graph TD
    subgraph "User Layer"
        A[Natural Language] --> B[any-mcp-cli]
        A2[Tool Calls] --> B
        A3[Web Requests] --> C[any-mcp Web API]
    end
    
    subgraph "any-mcp Package"
        B --> D[CLI Interface]
        C --> E[API Layer]
        D --> F[Core Engine]
        E --> F
        F --> G[MCP Manager]
        F --> H[Tool Manager]
        F --> I[LLM Service]
    end
    
    subgraph "Core Modules"
        G --> J[Manager Layer]
        H --> K[Tool Discovery]
        I --> L[Claude/Gemini]
        J --> M[Installer]
        J --> N[Lifecycle]
    end
    
    subgraph "MCP Integration"
        M --> O[Git MCP]
        M --> P[Filesystem MCP]
        M --> Q[GitHub MCP]
        M --> R[Any MCP...]
    end
    
    subgraph "External Services"
        O --> S[Git Operations]
        P --> T[File System]
        Q --> U[GitHub API]
        R --> V[Any API]
    end
    
    %% Config
    W[config/mcp_config.yaml] --> G
    
    %% Styling
    style B fill:#e1f5fe
    style F fill:#f3e5f5
    style I fill:#e8f5e8
    style G fill:#fff3e0
```

### Core Components

1. **CLI Interface** (`any_mcp/cli/main.py`) - Command-line interface with natural language processing for tool calls
2. **Core Engine** (`any_mcp/main.py`) - Main application logic and MCP orchestration
3. **MCP Manager** (`any_mcp/managers/manager.py`) - Lifecycle management, health monitoring, and tool orchestration
4. **MCP Installer** (`any_mcp/managers/installer.py`) - Multi-source MCP package installer (Docker, local files, Python modules)
5. **MCP Client** (`any_mcp/core/client.py`) - Enhanced client with tool discovery and calling capabilities
6. **Web API** (`any_mcp/api/web_mcp.py`) - FastAPI-based HTTP interface for remote MCP operations
7. **LLM Integration** (`any_mcp/core/claude.py`, `any_mcp/core/gemini.py`) - Claude and Gemini support for natural language processing
8. **Tool Management** (`any_mcp/core/tools.py`) - Centralized tool discovery and management across all MCPs
9. **Chat Interface** (`any_mcp/core/chat.py`, `any_mcp/core/cli_chat.py`) - LLM-powered chat and conversation management
10. **Server Connector** (`any_mcp/servers/connect_server.py`) - Flexible server connection interface

## Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/chi-n-nguyen/any-mcp.git
cd any-mcp

# Install dependencies
pip install -e .

# Copy example configuration
cp config/example_mcp_config.yaml config/mcp_config.yaml

# Set environment variables (optional)
export GITHUB_TOKEN=your_github_token_here
export USE_UV=1  # Use uv for faster Python execution
```

### Quick Start with v1.0.0 Release

```bash
# Download the latest release
wget https://github.com/chi-n-nguyen/any-mcp/archive/refs/tags/v1.0.0.tar.gz
tar -xzf v1.0.0.tar.gz
cd any-mcp-1.0.0

# Install and run
pip install -e .
python main.py
```

### Basic Usage

#### 1. Natural Language CLI (Recommended)

```bash
# Natural language tool call via configured MCPs
any-mcp-cli nl --module mcp_server_git --query "show git status repo_path=."

# Explicit tool calls
any-mcp-cli call --module mcp_server_git --tool git_status --args repo_path=.

# Interactive chat (requires Claude or Gemini API key)
any-mcp-cli chat --module mcp_server_git
```

#### 2. Server Management

```bash
# List configured servers
any-mcp-cli list

# Install and configure MCPs
any-mcp-cli install --name docs --source local://my_mcp.py --desc "Document operations"
any-mcp-cli install --name git --source docker://git-mcp-image --desc "Git operations"

# Start/stop servers
any-mcp-cli start --server docs
any-mcp-cli tools --server docs
any-mcp-cli stop --server docs
```

#### 3. Web API Server

```bash
# Start the web API server
python -m any_mcp.api.web_mcp

# Or use uvicorn directly
uvicorn any_mcp.api.web_mcp:app --host 0.0.0.0 --port 8000 --reload
```

#### 4. Programmatic Usage

```python
from any_mcp.managers.manager import MCPManager
from any_mcp.managers.installer import MCPInstaller

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

# Install a new MCP (example: Git MCP)
curl -X POST http://localhost:8000/mcp/install \
  -H "Content-Type: application/json" \
  -d '{
    "name": "git",
    "source": "module://mcp_server_git",
    "description": "Git operations via MCP"
  }'

# Call a tool (example)
curl -X POST http://localhost:8000/mcp/git/call \
  -H "Content-Type: application/json" \
  -d '{
    "tool_name": "git_status",
    "args": {"repo_path": "."}
  }'

# Check MCP health
curl http://localhost:8000/mcp/git/health
```

## Configuration

Create a `config/mcp_config.yaml` file to define your MCPs:

```yaml
installed_mcps:
  github:
    type: "docker"
    source: "ghcr.io/github/github-mcp-server"
    description: "GitHub's official MCP server"
    env_vars:
      GITHUB_PERSONAL_ACCESS_TOKEN: "${GITHUB_TOKEN}"
    enabled: true

  # Add your custom MCPs here
  # my_mcp:
  #   type: "local"
  #   source: "./my_custom_mcp.py"
  #   description: "My custom MCP server"
  #   enabled: true
```

## Supported MCP Sources

### Python Module MCPs
```bash
# Use Python modules directly (recommended for community MCPs)
any-mcp-cli call --module mcp_server_git --tool git_status --args repo_path=.
any-mcp-cli nl --module mcp_server_filesystem --query "list files path=/tmp"
```

### Docker MCPs
```bash
# Install from Docker registry
any-mcp-cli install --name github --source docker://ghcr.io/github/github-mcp-server
any-mcp-cli call --docker ghcr.io/github/github-mcp-server --tool search_repos --args query=python
```

### Local Script MCPs
```bash
# Use local Python scripts
any-mcp-cli call --script my_local_mcp.py --tool read_document --args doc_id=plan.md
any-mcp-cli nl --script custom_mcp.py --query "process data: input=test.csv"
```

### Registry MCPs (Future)
```bash
# Install from MCP registry (planned)
python any_mcp_cli.py install --name financial --source registry://financial-data-mcp
```

## Examples and Demos

### Quick Start Examples

```bash
# External Git MCP operations
python -m pip install mcp-server-git
any-mcp-cli call --module mcp_server_git --tool git_status --args repo_path=.

# Community filesystem MCP
python -m pip install mcp-server-filesystem  
any-mcp-cli nl --module mcp_server_filesystem --query "list directory contents path=."
```

### Available Community MCPs

Install and use any MCP from the [official servers repository](https://github.com/modelcontextprotocol/servers):

```bash
# Git operations
pip install mcp-server-git
python any_mcp_cli.py call --module mcp_server_git --tool git_log --args repo_path=.

# Filesystem operations  
pip install mcp-server-filesystem
python any_mcp_cli.py call --module mcp_server_filesystem --tool read_file --args path=README.md

# Database operations
pip install mcp-server-sqlite
python any_mcp_cli.py call --module mcp_server_sqlite --tool execute_query --args query="SELECT * FROM users"

# Notion workspace integration (included)
python any_mcp_cli.py call --script notion_mcp_server.py --tool get_task_tracker_tasks --args status_filter=in_progress
python any_mcp_cli.py nl --script notion_mcp_server.py --query "Show me my course notes"
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
any_mcp/
├── any_mcp/
│   ├── api/               # Web API implementation
│   │   └── web_mcp.py
│   ├── core/              # Core functionality
│   │   ├── chat.py
│   │   ├── claude.py
│   │   ├── gemini.py
│   │   ├── cli_chat.py
│   │   ├── cli.py
│   │   ├── tools.py
│   │   └── error_handling.py
│   ├── managers/          # MCP lifecycle & installation
│   │   ├── manager.py
│   │   └── installer.py
│   ├── servers/
│   │   └── connect_server.py
│   └── cli/
│       └── main.py
├── config/
│   └── mcp_config.yaml
├── main.py                # Entry point
├── README.md
├── LICENSE
└── VERSION
```

## Release Notes

### v1.0.0 - First Production Release (2025-01-08)

**Major Milestone**: First stable release ready for production deployment and LLMGine integration.

** New Features:**
- Universal MCP adapter with auto-discovery and tool orchestration
- Multi-LLM support for Claude and Gemini with unified interface
- Natural language processing for any MCP without API knowledge
- RESTful Web API with comprehensive endpoints for remote management
- Notion workspace integration with task tracking and database queries
- Production-ready configuration management and health monitoring
- LLMGine-compatible deployment with secure environment handling

** Technical Improvements:**
- Standard MCP protocol compliance for seamless integration
- Health check endpoints for monitoring and diagnostics
- Secure environment variable configuration (no hardcoded secrets)
- Docker and local deployment support with launcher scripts
- Comprehensive error handling and logging throughout the stack
- Multi-source MCP installation (Docker, local files, Python modules)

** Documentation:**
- Complete setup and deployment guides
- LLMGine integration instructions with configuration examples
- API documentation with cURL examples and JavaScript integration
- Security best practices and environment variable management

**🔒 Security:**
- All sensitive data moved to environment variables
- Git history cleaned of any hardcoded secrets
- Production-ready secret management practices

This release establishes any-mcp as a stable, production-ready platform for MCP integration with modern LLM systems.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.


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
export LLM_PROVIDER=gemini  # or 'claude'
export CLAUDE_MODEL=claude-3-sonnet-20240229
export ANTHROPIC_API_KEY=your_anthropic_key
export GEMINI_MODEL=gemini-1.5-pro
export GEMINI_API_KEY=your_gemini_key
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
CMD ["uvicorn", "any_mcp.api.web_mcp:app", "--host", "0.0.0.0", "--port", "8000"]
```

<!-- Notion/demo content removed during cleanup to reflect universal MCP usage only -->

#### Setting Up Notion MCP Server

The project includes a Notion MCP server (`notion_mcp_server.py`) that enables natural language queries to your Notion workspace.

**1. Get Your Notion Integration Key:**
- Go to [Notion Integrations](https://www.notion.so/my-integrations)
- Create a new integration and copy the key
- Share your databases/pages with the integration
- Set the API key as an environment variable:
  ```bash
  export NOTION_API_KEY=your_notion_integration_key_here
  ```

**2. Test Direct Tool Calls:**
```bash
# Activate virtual environment (if not already active)
source .venv/bin/activate

# Get all tasks from your Task Tracker
uv run python3 any_mcp_cli.py call --script notion_mcp_server.py --tool get_task_tracker_tasks --args status_filter=all

# Get tasks by status
uv run python3 any_mcp_cli.py call --script notion_mcp_server.py --tool get_task_tracker_tasks --args status_filter=in_progress

# Get database contents
uv run python3 any_mcp_cli.py call --script notion_mcp_server.py --tool get_database_contents --args database_id=YOUR_DATABASE_ID

# Get specific page content
uv run python3 any_mcp_cli.py call --script notion_mcp_server.py --tool get_page_content --args page_id=YOUR_PAGE_ID
```

**3. Enable Natural Language Queries:**

Create a `.env` file with your LLM provider:
```bash
# For Gemini (recommended - free tier available)
echo "LLM_PROVIDER=gemini" > .env
echo "GEMINI_API_KEY=your_gemini_api_key_here" >> .env

# OR for Claude
echo "LLM_PROVIDER=claude" > .env
echo "ANTHROPIC_API_KEY=your_anthropic_key_here" >> .env
```

**4. Use Natural Language Queries:**
```bash
# Ask questions in plain English
uv run python3 any_mcp_cli.py nl --script notion_mcp_server.py --query "What are my high priority tasks due this month?"

uv run python3 any_mcp_cli.py nl --script notion_mcp_server.py --query "Show me all my course notes from COMP20008"

uv run python3 any_mcp_cli.py nl --script notion_mcp_server.py --query "What goals do I have that are marked as done?"
```

**5. Interactive Chat Mode:**
```bash
# Start interactive session with Notion
uv run python3 any_mcp_cli.py chat --script notion_mcp_server.py
```

**6. Web API Access:**

Start the web server:
```bash
# Start web server
uv run python3 -m api.web_mcp
```

**RESTful API Endpoints:**
```bash
# Check API health
curl http://localhost:8000/health

# List all MCPs
curl http://localhost:8000/mcp

# List tools for specific MCP
curl http://localhost:8000/mcp/notion_custom/tools

# Call Notion tools via HTTP
curl -X POST http://localhost:8000/mcp/notion_custom/call \
  -H "Content-Type: application/json" \
  -d '{"tool_name": "get_task_tracker_tasks", "args": {"status_filter": "all"}}'

# Get high priority tasks
curl -X POST http://localhost:8000/mcp/notion_custom/call \
  -H "Content-Type: application/json" \
  -d '{"tool_name": "get_task_tracker_tasks", "args": {"status_filter": "in_progress"}}'

# Query specific database
curl -X POST http://localhost:8000/mcp/notion_custom/call \
  -H "Content-Type: application/json" \
  -d '{"tool_name": "get_database_contents", "args": {"database_id": "YOUR_DATABASE_ID"}}'

# Search Notion content
curl -X POST http://localhost:8000/mcp/notion_custom/call \
  -H "Content-Type: application/json" \
  -d '{"tool_name": "search_notion", "args": {"query": "MCP", "filter_type": "page"}}'
```

**Web Interface Demo:**
Open `notion_web_demo.html` in your browser for an interactive web interface to test the API.

**JavaScript/Web Integration:**
```javascript
// Example web app integration
async function getMyTasks() {
    const response = await fetch('http://localhost:8000/mcp/notion_custom/call', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            tool_name: 'get_task_tracker_tasks',
            args: { status_filter: 'all' }
        })
    });
    const data = await response.json();
    const tasks = JSON.parse(data.data.content[0].text);
    return tasks;
}
```

**Available Notion Tools:**
- `search_notion` - Search across all accessible content
- `get_database_contents` - Get contents from a specific database
- `get_page_content` - Get content of a specific page
- `get_task_tracker_tasks` - Get tasks with status filtering
- `health_check` - Health check for LLMGine integration

### LLMGine Integration

The project is ready for LLMGine integration with standard MCP protocol compliance:

**Quick Setup for LLMGine:**
```bash
# Set your Notion API key
export NOTION_API_KEY=your_notion_integration_key_here

# Use the launcher script
./launch_notion_mcp.sh

# Or directly
python3 notion_mcp_server.py
```

**LLMGine Configuration:**
```json
{
  "mcpServers": {
    "notion": {
      "command": "./launch_notion_mcp.sh",
      "cwd": "/path/to/any-mcp",
      "description": "Notion workspace integration with task tracking"
    }
  }
}
```

**Health Check:**
```bash
echo '{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"health_check","arguments":{}}}' | python3 notion_mcp_server.py
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
