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

# Set up environment variables at module level
os.environ["NOTION_API_TOKEN"] = "secret_Ys8Vd37lj1WMuMWz0lx0WkW88yRz4NBbj4XH5PiseC4"

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
