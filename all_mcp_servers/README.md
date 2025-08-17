# MCP Server Examples

This directory contains example MCP server implementations that demonstrate best practices and common patterns for building your own MCP servers.

## Available Examples

### `notion_mcp_server.py` - Comprehensive Template

A complete Notion MCP server implementation that demonstrates:

- **MCP Protocol Compliance**: Proper JSON-RPC handling and tool registration
- **External API Integration**: HTTP client setup, authentication, error handling
- **Tool Implementation**: Multiple tool types with different input schemas
- **Error Handling**: Comprehensive error handling and user feedback
- **Documentation**: Extensive comments explaining each component

**Tools Provided:**
- `search_notion` - Search across Notion content
- `get_page_content` - Retrieve specific page content
- `get_database_contents` - Query database entries with filtering
- `create_page` - Create new pages with content
- `health_check` - Server health and API connectivity check

**Usage:**
```bash
# Set up environment
export NOTION_API_TOKEN=your_notion_integration_token

# Test the server
any-mcp-cli call --script examples/notion_mcp_server.py --tool health_check
any-mcp-cli call --script examples/notion_mcp_server.py --tool search_notion --args query="project notes"
```

### `discord_mcp_server.py` - Discord Integration

A Discord MCP server that enables LLMs to interact with Discord channels, allowing them to send and read messages through Discord's API. This server provides a Python bridge to a TypeScript backend for seamless Discord integration.

**Features:**
- Send messages to Discord channels
- Read recent messages from channels
- Automatic server and channel discovery
- Support for both channel names and IDs
- Proper error handling and validation

**Tools Provided:**
- `send_message` - Send messages to Discord channels
- `read_messages` - Read recent messages from channels
- `get_guilds` - Get available Discord guilds
- `health_check` - Server health and Discord API connectivity check

**Prerequisites:**
- Node.js 16.x or higher
- A Discord bot token
- The bot must be invited to your server with proper permissions:
  - Read Messages/View Channels
  - Send Messages
  - Read Message History

**Setup:**
1. Install Node.js dependencies in the discord_mcp_server directory:
```bash
cd all_mcp_servers/discord_mcp_server
npm install
```

2. Set up your Discord bot token:
```bash
export DISCORD_BOT_TOKEN=your_discord_bot_token_here
```

3. Test the server:
```bash
any-mcp-cli call --script all_mcp_servers/discord_mcp_server.py --tool health_check
any-mcp-cli call --script all_mcp_servers/discord_mcp_server.py --tool get_guilds
```

**Usage Examples:**
```bash
# Send a message to a channel
any-mcp-cli call --script all_mcp_servers/discord_mcp_server.py --tool send_message --args channel="general" message="Hello from MCP!"

# Read recent messages
any-mcp-cli call --script all_mcp_servers/discord_mcp_server.py --tool read_messages --args channel="general" limit=10
```

**Architecture:**
This server uses a Python-Node.js bridge approach:
- Python handles MCP protocol and tool registration
- TypeScript backend manages Discord API interactions
- Subprocess communication between the two languages
- Maintains compatibility with existing MCP tooling

## Using Examples as Templates

1. **Copy the example**: `cp examples/notion_mcp_server.py examples/your_service_mcp.py`
2. **Replace API calls**: Update URLs, headers, and request/response handling for your service
3. **Update tools**: Modify the tool definitions and implement your service's functionality
4. **Test thoroughly**: Use `any-mcp-cli` to test your implementation
5. **Add to config**: Include your MCP in `config/mcp_config.yaml`

## Common Integration Patterns

The Notion example demonstrates patterns that apply to most API integrations:

- **Authentication**: Environment variable configuration and header setup
- **Request Handling**: Timeout, error checking, and response parsing
- **Tool Design**: Clear input schemas and structured output formats
- **Health Checks**: Connectivity testing and status reporting

The Discord example shows additional patterns for:
- **Multi-language Integration**: Bridging Python MCP with other language backends
- **External Process Communication**: Using subprocess for language interoperability
- **Real-time API Handling**: Managing persistent connections and state

Use these patterns when building MCPs for other services like Slack, Jira, GitHub, databases, or cloud platforms.

## Testing Your MCP

All examples can be tested using the any-mcp-cli:

```bash
# List available tools
any-mcp-cli call --script examples/your_mcp.py --tool health_check

# Test specific functionality
any-mcp-cli call --script examples/your_mcp.py --tool tool_name --args param=value

# Natural language interface
any-mcp-cli nl --script examples/your_mcp.py --query "do something with test data"
```

## Contributing Examples

When contributing new examples:

1. Follow the same documentation and error handling patterns
2. Include a comprehensive `health_check` tool
3. Use environment variables for all credentials
4. Add clear docstrings and comments
5. Test with `any-mcp-cli` before submitting
6. For multi-language integrations, document setup requirements clearly
