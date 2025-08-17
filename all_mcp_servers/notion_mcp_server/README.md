# Notion MCP Server

## Directory Structure

```
notion_mcp_server/
├── __init__.py                    # Package exports: NotionMCPServer, main
├── main.py                        # Entry point: main()
├── server.py                      # Core server: NotionMCPServer class
├── handlers/
│   ├── __init__.py               # Handler exports
│   ├── base.py                   # BaseHandler: get_notion_headers()
│   ├── search.py                 # SearchHandler: search_notion()
│   ├── pages.py                  # PagesHandler: get_page_content(), create_page()
│   ├── databases.py              # DatabasesHandler: get_database_contents()
│   └── health.py                 # HealthHandler: health_check()
└── utils/
    ├── __init__.py               # Utils exports
    ├── config.py                 # Configuration: get_notion_token(), constants
    ├── notion_client.py          # NotionClient: get_notion_headers()
    └── extractors.py             # Helpers: extract_title(), extract_properties()
```

## File Details

### Core Files
- **`main.py`** - Server loop, stdin/stdout handling, JSON-RPC message processing
  - `main()` - Main async loop
- **`server.py`** - Main API interface, tool routing, handler coordination  
  - `NotionMCPServer` class with 5 main functions + `handle_request()`
- **`__init__.py`** - Package exports for external imports

### Handlers (Business Logic)
- **`base.py`** - Common handler functionality
  - `BaseHandler.get_notion_headers()`
- **`search.py`** - Search operations
  - `SearchHandler.search_notion()`
- **`pages.py`** - Page operations  
  - `PagesHandler.get_page_content()`, `PagesHandler.create_page()`
- **`databases.py`** - Database operations
  - `DatabasesHandler.get_database_contents()`  
- **`health.py`** - Health check operations
  - `HealthHandler.health_check()`

### Utils (Shared Components)
- **`config.py`** - Configuration management, token handling
  - `get_notion_token()`, constants
- **`notion_client.py`** - Notion API wrapper
  - `NotionClient.get_notion_headers()`
- **`extractors.py`** - Data extraction utilities
  - `extract_title()`, `extract_properties()`

## Flow & Architecture

### Entry Point Flow
```
main_file.py → notion_mcp_server/main.py → NotionMCPServer → Handlers → Utils
```

### 1. **Entry Point** (`main_file.py`)
- Imports and runs `main()` from `notion_mcp_server/main.py`
- Handles dependencies check

### 2. **Server Loop** (`notion_mcp_server/main.py`)
- Creates `NotionMCPServer` instance
- Runs stdin/stdout JSON-RPC loop
- Routes messages to server's `handle_request()`

### 3. **Core Server** (`notion_mcp_server/server.py`)
- **NotionMCPServer class** - Main API interface
- Loads tools via `load_all_tools()`
- Creates handler instances
- Routes tool calls to appropriate handlers
- **5 Main Functions**: `search_notion()`, `get_page_content()`, `get_database_contents()`, `create_page()`, `health_check()`

### 4. **Handlers** (`notion_mcp_server/handlers/`)
- **SearchHandler** - Wraps `search_notion()` logic
- **PagesHandler** - Wraps `get_page_content()`, `create_page()` logic  
- **DatabasesHandler** - Wraps `get_database_contents()` logic
- **HealthHandler** - Wraps `health_check()` logic
- All extend **BaseHandler** for common functionality

### 5. **Utils** (`notion_mcp_server/utils/`)
- **config.py** - Configuration & token management
- **notion_client.py** - Notion API headers wrapper
- **extractors.py** - `extract_title()`, `extract_properties()` helpers

## Request Flow Example
```
External Code
    ↓ calls server.search_notion()
NotionMCPServer 
    ↓ delegates to self.search_handler.search_notion()
SearchHandler
    ↓ uses self.get_notion_headers() from BaseHandler
    ↓ uses extract_title() from utils
    ↓ makes API call to Notion
    ↓ returns formatted response
```

## File Responsibilities
- **Main**: Server loop & JSON-RPC handling
- **Server**: Tool routing & API interface  
- **Handlers**: Business logic execution
- **Utils**: Shared utilities & configuration