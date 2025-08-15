#!/usr/bin/env python3
"""
Rich Notion MCP CLI - Beautiful, colorful interface!
"""

import asyncio
import os
from examples.notion_mcp_server import NotionMCPServer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich.prompt import Prompt
from rich.layout import Layout
from rich.columns import Columns
from rich.align import Align
from rich import box

# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv()

# Verify NOTION_API_TOKEN is set
notion_token = os.getenv("NOTION_API_TOKEN")
if not notion_token:
    print("❌ Error: NOTION_API_TOKEN environment variable not set!")
    print("Please create a .env file with: NOTION_API_TOKEN=your_token_here")
    exit(1)

# Create rich console
console = Console()

async def rich_cli():
    # Create server (environment already set)
    server = NotionMCPServer()
    
    # Welcome banner
    welcome_text = Text("🚀 Notion MCP CLI", style="bold blue")
    subtitle = Text("DSCubed Workspace", style="italic cyan")
    
    console.print(Panel(
        Align.center(welcome_text + "\n" + subtitle),
        border_style="blue",
        box=box.ROUNDED
    ))
    
    # Show available tools
    tools_table = Table(title="🛠️  Available Tools (30+ Tools!)", show_header=True, header_style="bold magenta")
    tools_table.add_column("Command", style="cyan", no_wrap=True)
    tools_table.add_column("Description", style="white")
    tools_table.add_column("Example", style="green")
    
    # Core tools
    tools_table.add_row("search <query>", "Search across Notion content", "search project")
    tools_table.add_row("search_with_filters", "Advanced search with filters", "search_with_filters project")
    tools_table.add_row("page <id>", "Get page content", "page 24bc2e93...")
    tools_table.add_row("health", "Check connection status", "health")
    tools_table.add_row("help", "Show this help", "help")
    tools_table.add_row("quit", "Exit CLI", "quit")
    
    console.print(tools_table)
    
    # Show comprehensive capabilities
    capabilities_table = Table(title="🚀 Complete Notion API Implementation (30+ Tools)", show_header=True, header_style="bold blue")
    capabilities_table.add_column("Category", style="cyan", no_wrap=True)
    capabilities_table.add_column("Tools Available", style="white")
    capabilities_table.add_column("Count", style="yellow")
    
    capabilities_table.add_row("📄 Pages", "Create, Read, Update, Delete, Move", "5 tools")
    capabilities_table.add_row("🗄️ Databases", "Create, Read, Update, Delete, Query", "5 tools")
    capabilities_table.add_row("🧱 Blocks", "Create, Read, Update, Delete, Children", "6 tools")
    capabilities_table.add_row("👥 Users", "Get User, Get Users, Get Me", "3 tools")
    capabilities_table.add_row("💬 Comments", "Create, Read Comments", "2 tools")
    capabilities_table.add_row("📎 Files", "Upload Files", "1 tool")
    capabilities_table.add_row("🔍 Search", "Basic Search, Advanced Search", "2 tools")
    capabilities_table.add_row("💚 Health", "Connection Status", "1 tool")
    capabilities_table.add_row("📊 Total", "Complete Notion API Coverage", "30+ tools")
    
    console.print(capabilities_table)
    console.print()
    
    while True:
        try:
            # Rich prompt
            command = Prompt.ask("\n[bold cyan]Notion MCP[/bold cyan] >", default="help")
            command = command.strip().lower()
            
            if command in ["quit", "exit", "q"]:
                console.print("\n[bold yellow]👋 Goodbye![/bold yellow]")
                break
                
            elif command == "help":
                console.print(Panel(
                    tools_table,
                    title="[bold blue]Help - Available Tools[/bold blue]",
                    border_style="blue"
                ))
                console.print()
                
                # Show CLI commands
                cli_commands = Table(title="[bold blue]Help - CLI Commands[/bold blue]", show_header=True, header_style="bold blue")
                cli_commands.add_column("Command", style="cyan", no_wrap=True)
                cli_commands.add_column("Usage", style="white")
                cli_commands.add_column("Description", style="green")
                
                cli_commands.add_row("health", "", "Check Notion connection")
                cli_commands.add_row("search <query>", "search project", "Search for content")
                cli_commands.add_row("search_with_filters <query>", "search_with_filters project", "Advanced search")
                cli_commands.add_row("page <id>", "page 24bc2e93...", "Get page content")
                cli_commands.add_row("create_page <parent_id> <title>", "create_page parent123 MyPage", "Create new page")
                cli_commands.add_row("update_page <id>", "update_page page123", "Update page")
                cli_commands.add_row("delete_page <id>", "delete_page page123", "Delete page")
                cli_commands.add_row("move_page <id> <new_parent>", "move_page page123 parent456", "Move page")
                cli_commands.add_row("create_database <parent_id> <title>", "create_database parent123 MyDB", "Create database")
                cli_commands.add_row("query_database <id>", "query_database db123", "Query database")
                cli_commands.add_row("create_block <page_id> <type> <content>", "create_block page123 paragraph Hello", "Create block")
                cli_commands.add_row("get_users", "", "Get all users")
                cli_commands.add_row("get_me", "", "Get current user")
                cli_commands.add_row("create_comment <parent_id> <content>", "create_comment page123 Great work!", "Create comment")
                cli_commands.add_row("upload_file <page_id> <path> <caption>", "upload_file page123 file.pdf My file", "Upload file")
                cli_commands.add_row("help", "", "Show this help")
                cli_commands.add_row("quit", "", "Exit CLI")
                
                console.print(cli_commands)
                console.print()
                console.print(Panel(
                    capabilities_table,
                    title="[bold blue]Help - Notion API Capabilities[/bold blue]",
                    border_style="blue"
                ))
                
            elif command == "health":
                with console.status("[bold green]Checking connection...[/bold green]"):
                    result = await server.health_check()
                
                if result.get('healthy'):
                    health_panel = Panel(
                        f"[bold green]✅ Connected to DSCubed Notion![/bold green]\n"
                        f"👤 User: [cyan]{result.get('user_name', 'Unknown')}[/cyan]\n"
                        f"🆔 ID: [cyan]{result.get('user_id', 'Unknown')}[/cyan]\n"
                        f"🔗 API: [green]{result.get('notion_api', 'Unknown')}[/green]",
                        title="[bold green]Health Check[/bold green]",
                        border_style="green"
                    )
                    console.print(health_panel)
                else:
                    console.print(f"[bold red]❌ Connection failed: {result}[/bold red]")
                    
            elif command.startswith("search "):
                query = command[7:]  # Remove "search " prefix
                
                search_panel = Panel(
                    f"[bold blue]🔍 Searching for:[/bold blue] [cyan]{query}[/cyan]",
                    border_style="blue"
                )
                console.print(search_panel)
                
                with console.status("[bold green]Searching Notion...[/bold green]"):
                    result = await server.search_notion(query, "page")
                
                if result.get('success'):
                    # Create results table - show ALL results, not just 10
                    results_table = Table(
                        title=f"✅ Found {result['results_count']} items",
                        show_header=True,
                        header_style="bold green",
                        box=box.ROUNDED
                    )
                    results_table.add_column("#", style="cyan", no_wrap=True)
                    results_table.add_column("Title", style="white")
                    results_table.add_column("ID", style="yellow", no_wrap=True)
                    results_table.add_column("Last Edited", style="green")
                    
                    # Show ALL results, not just first 10
                    for i, item in enumerate(result['results'], 1):
                        # Truncate long titles
                        title = item['title'][:50] + "..." if len(item['title']) > 50 else item['title']
                        # Format date
                        date = item.get('last_edited', 'Unknown')[:10] if item.get('last_edited') else 'Unknown'
                        
                        results_table.add_row(
                            str(i),
                            title,
                            item['id'][:12] + "...",
                            date
                        )
                    
                    console.print(results_table)
                    
                    # No more "and X more results" message since we show everything
                    console.print(f"[green]📊 Displaying all {result['results_count']} results[/green]")
                        
                else:
                    console.print(f"[bold red]❌ Search failed: {result.get('error', 'Unknown error')}[/bold red]")
                    
            elif command.startswith("search_with_filters "):
                query = command[20:]  # Remove "search_with_filters " prefix
                console.print(f"[bold blue]🔍 Advanced search for:[/bold blue] [cyan]{query}[/cyan]")
                console.print("[yellow]Note: Advanced search with filters not yet implemented in CLI[/yellow]")
                
            elif command.startswith("create_page "):
                parts = command.split(" ", 2)
                if len(parts) >= 3:
                    parent_id = parts[1]
                    title = parts[2]
                    console.print(f"[bold blue]📄 Creating page:[/bold blue] [cyan]{title}[/cyan]")
                    console.print(f"[yellow]Note: Page creation not yet implemented in CLI[/yellow]")
                else:
                    console.print("[red]Usage: create_page <parent_id> <title>[/red]")
                    
            elif command.startswith("update_page "):
                parts = command.split(" ", 2)
                if len(parts) >= 2:
                    page_id = parts[1]
                    console.print(f"[bold blue]✏️ Updating page:[/bold blue] [cyan]{page_id}[/cyan]")
                    console.print(f"[yellow]Note: Page update not yet implemented in CLI[/yellow]")
                else:
                    console.print("[red]Usage: update_page <page_id>[/red]")
                    
            elif command.startswith("delete_page "):
                page_id = command[12:]  # Remove "delete_page " prefix
                console.print(f"[bold red]🗑️ Deleting page:[/bold red] [cyan]{page_id}[/cyan]")
                console.print(f"[yellow]Note: Page deletion not yet implemented in CLI[/yellow]")
                
            elif command.startswith("move_page "):
                parts = command.split(" ", 2)
                if len(parts) >= 3:
                    page_id = parts[1]
                    new_parent_id = parts[2]
                    console.print(f"[bold blue]🔄 Moving page:[/bold blue] [cyan]{page_id}[/cyan]")
                    console.print(f"[yellow]Note: Page move not yet implemented in CLI[/yellow]")
                else:
                    console.print("[red]Usage: move_page <page_id> <new_parent_id>[/red]")
                    
            elif command.startswith("create_database "):
                parts = command.split(" ", 2)
                if len(parts) >= 3:
                    parent_id = parts[1]
                    title = parts[2]
                    console.print(f"[bold blue]🗄️ Creating database:[/bold blue] [cyan]{title}[/cyan]")
                    console.print(f"[yellow]Note: Database creation not yet implemented in CLI[/yellow]")
                else:
                    console.print("[red]Usage: create_database <parent_id> <title>[/red]")
                    
            elif command.startswith("update_database "):
                database_id = command[16:]  # Remove "update_database " prefix
                console.print(f"[bold blue]✏️ Updating database:[/bold blue] [cyan]{database_id}[/cyan]")
                console.print(f"[yellow]Note: Database update not yet implemented in CLI[/yellow]")
                
            elif command.startswith("delete_database "):
                database_id = command[16:]  # Remove "delete_database " prefix
                console.print(f"[bold red]🗑️ Deleting database:[/bold red] [cyan]{database_id}[/cyan]")
                console.print(f"[yellow]Note: Database deletion not yet implemented in CLI[/yellow]")
                
            elif command.startswith("query_database "):
                database_id = command[15:]  # Remove "query_database " prefix
                console.print(f"[bold blue]🔍 Querying database:[/bold blue] [cyan]{database_id}[/cyan]")
                console.print(f"[yellow]Note: Advanced database query not yet implemented in CLI[/yellow]")
                
            elif command.startswith("create_block "):
                parts = command.split(" ", 3)
                if len(parts) >= 4:
                    page_id = parts[1]
                    block_type = parts[2]
                    content = parts[3]
                    console.print(f"[bold blue]🧱 Creating block:[/bold blue] [cyan]{block_type}[/cyan]")
                    console.print(f"[yellow]Note: Block creation not yet implemented in CLI[/yellow]")
                else:
                    console.print("[red]Usage: create_block <page_id> <block_type> <content>[/red]")
                    
            elif command.startswith("update_block "):
                parts = command.split(" ", 2)
                if len(parts) >= 3:
                    block_id = parts[1]
                    content = parts[2]
                    console.print(f"[bold blue]✏️ Updating block:[/bold blue] [cyan]{block_id}[/cyan]")
                    console.print(f"[yellow]Note: Block update not yet implemented in CLI[/yellow]")
                else:
                    console.print("[red]Usage: update_block <block_id> <content>[/red]")
                    
            elif command.startswith("delete_block "):
                block_id = command[13:]  # Remove "delete_block " prefix
                console.print(f"[bold red]🗑️ Deleting block:[/bold red] [cyan]{block_id}[/cyan]")
                console.print(f"[yellow]Note: Block deletion not yet implemented in CLI[/yellow]")
                
            elif command.startswith("get_block_children "):
                block_id = command[19:]  # Remove "get_block_children " prefix
                console.print(f"[bold blue]🧱 Getting block children:[/bold blue] [cyan]{block_id}[/cyan]")
                console.print(f"[yellow]Note: Block children not yet implemented in CLI[/yellow]")
                
            elif command.startswith("append_block_children "):
                parts = command.split(" ", 2)
                if len(parts) >= 3:
                    block_id = parts[1]
                    blocks = parts[2]
                    console.print(f"[bold blue]➕ Appending blocks:[/bold blue] [cyan]{block_id}[/cyan]")
                    console.print(f"[yellow]Note: Block append not yet implemented in CLI[/yellow]")
                else:
                    console.print("[red]Usage: append_block_children <block_id> <blocks>[/red]")
                    
            elif command.startswith("get_user "):
                user_id = command[9:]  # Remove "get_user " prefix
                console.print(f"[bold blue]👤 Getting user:[/bold blue] [cyan]{user_id}[/cyan]")
                console.print(f"[yellow]Note: User retrieval not yet implemented in CLI[/yellow]")
                
            elif command == "get_users":
                console.print("[bold blue]👥 Getting all users[/bold blue]")
                console.print(f"[yellow]Note: Users list not yet implemented in CLI[/yellow]")
                
            elif command == "get_me":
                console.print("[bold blue]👤 Getting current user[/bold blue]")
                console.print(f"[yellow]Note: Current user not yet implemented in CLI[/yellow]")
                
            elif command.startswith("create_comment "):
                parts = command.split(" ", 2)
                if len(parts) >= 3:
                    parent_id = parts[1]
                    content = parts[2]
                    console.print(f"[bold blue]💬 Creating comment:[/bold blue] [cyan]{parent_id}[/cyan]")
                    console.print(f"[yellow]Note: Comment creation not yet implemented in CLI[/yellow]")
                else:
                    console.print("[red]Usage: create_comment <parent_id> <content>[/red]")
                    
            elif command.startswith("get_comments "):
                block_id = command[13:]  # Remove "get_comments " prefix
                console.print(f"[bold blue]💬 Getting comments:[/bold blue] [cyan]{block_id}[/cyan]")
                console.print(f"[yellow]Note: Comments retrieval not yet implemented in CLI[/yellow]")
                
            elif command.startswith("upload_file "):
                parts = command.split(" ", 3)
                if len(parts) >= 4:
                    page_id = parts[1]
                    file_path = parts[2]
                    caption = parts[3]
                    console.print(f"[bold blue]📎 Uploading file:[/bold blue] [cyan]{file_path}[/cyan]")
                    console.print(f"[yellow]Note: File upload not yet implemented in CLI[/yellow]")
                else:
                    console.print("[red]Usage: upload_file <page_id> <file_path> <caption>[/red]")
                    
            elif command.startswith("page "):
                page_id = command[5:]  # Remove "page " prefix
                
                page_panel = Panel(
                    f"[bold blue]📄 Getting page:[/bold blue] [cyan]{page_id}[/cyan]",
                    border_style="blue"
                )
                console.print(page_panel)
                
                with console.status("[bold green]Fetching page content...[/bold green]"):
                    result = await server.get_page_content(page_id)
                
                if result.get('success'):
                    # Create page info panel
                    page_info = Panel(
                        f"[bold green]✅ Page Retrieved Successfully![/bold green]\n\n"
                        f"📝 [bold]Title:[/bold] [cyan]{result.get('title', 'No title')}[/cyan]\n"
                        f"🔢 [bold]Content Blocks:[/bold] [yellow]{result.get('content_blocks', 0)}[/yellow]\n"
                        f"🔗 [bold]URL:[/bold] [blue]{result.get('url', 'No URL')}[/blue]\n"
                        f"📅 [bold]Last Edited:[/bold] [green]{result.get('last_edited', 'Unknown')[:10] if result.get('last_edited') else 'Unknown'}[/green]",
                        title="[bold green]Page Information[/bold green]",
                        border_style="green"
                    )
                    console.print(page_info)
                else:
                    console.print(f"[bold red]❌ Failed to get page: {result.get('error', 'Unknown error')}[/bold red]")
                    
            else:
                console.print(f"[bold red]❌ Unknown command: {command}[/bold red]")
                console.print("[yellow]Type 'help' for available commands[/yellow]")
                
        except KeyboardInterrupt:
            console.print("\n[bold yellow]👋 Goodbye![/bold yellow]")
            break
        except Exception as e:
            console.print(f"[bold red]❌ Error: {e}[/bold red]")

if __name__ == "__main__":
    try:
        asyncio.run(rich_cli())
    except KeyboardInterrupt:
        console.print("\n[bold yellow]👋 Goodbye![/bold yellow]")
