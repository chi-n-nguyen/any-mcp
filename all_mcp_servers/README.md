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
