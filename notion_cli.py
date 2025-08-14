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

# Create rich console
console = Console()

async def rich_cli():
    # Set up your API key
    os.environ["NOTION_API_TOKEN"] = "secret_Ys8Vd37lj1WMuMWz0lx0WkW88yRz4NBbj4XH5PiseC4"
    
    # Create server
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
    tools_table = Table(title="🛠️  Available Tools", show_header=True, header_style="bold magenta")
    tools_table.add_column("Command", style="cyan", no_wrap=True)
    tools_table.add_column("Description", style="white")
    tools_table.add_column("Example", style="green")
    
    tools_table.add_row("search <query>", "Search across Notion content", "search project")
    tools_table.add_row("page <id>", "Get page content", "page 24bc2e93...")
    tools_table.add_row("health", "Check connection status", "health")
    tools_table.add_row("help", "Show this help", "help")
    tools_table.add_row("quit", "Exit CLI", "quit")
    
    console.print(tools_table)
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
                    title="[bold blue]Help[/bold blue]",
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
                    # Create results table
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
                    
                    for i, item in enumerate(result['results'][:10], 1):
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
                    
                    if result['results_count'] > 10:
                        console.print(f"[yellow]... and {result['results_count'] - 10} more results[/yellow]")
                        
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
