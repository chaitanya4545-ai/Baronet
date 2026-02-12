"""
OpenClaw CLI Interface
Command-line interface for direct control
"""
import click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import print as rprint
import json

from core.openclaw import openclaw
from core.logger import log
from core.safety import safety
from core.ai_handler import create_ai_handler
from pathlib import Path

console = Console()


@click.group()
@click.version_option(version="0.1.0-phase1", prog_name="OpenClaw")
def cli():
    """
    OpenClaw - Personal Automation Engine
    
    Your central nervous system for automation tasks.
    """
    pass


@cli.command()
def status():
    """Show OpenClaw system status"""
    status_data = openclaw.get_status()
    
    panel = Panel(
        f"""[bold cyan]OpenClaw v{status_data['version']}[/bold cyan]
        
[yellow]Modules:[/yellow] {', '.join(status_data['modules'])}
[yellow]Workspace:[/yellow] {status_data['workspace']}
[yellow]Safety Status:[/yellow] {status_data['safety']['max_auto_permission']}
[yellow]Emergency Stop:[/yellow] {'🚨 ACTIVE' if status_data['safety']['emergency_stop'] else '✓ Inactive'}
        """,
        title="System Status",
        border_style="green"
    )
    console.print(panel)


@cli.command()
def help_commands():
    """List all available commands"""
    help_data = openclaw.get_help()
    
    table = Table(title="Available Commands", show_header=True, header_style="bold magenta")
    table.add_column("Module", style="cyan")
    table.add_column("Operations", style="green")
    
    for module, operations in help_data['available_modules'].items():
        table.add_row(module, ", ".join(operations))
    
    console.print(table)


@cli.group()
def file():
    """File operations"""
    pass


@file.command()
@click.argument('filename')
@click.argument('content', default="")
def create(filename, content):
    """Create a new file"""
    command = {
        'module': 'file',
        'operation': 'create',
        'args': {'filename': filename, 'content': content}
    }
    
    result = openclaw.execute(command)
    
    if result['success']:
        console.print(f"[green]✓[/green] Created: {result['path']}")
        console.print(f"  Size: {result['size']} bytes")
    else:
        console.print(f"[red]✗[/red] Error: {result['error']}")


@file.command()
@click.argument('filename')
def read(filename):
    """Read file contents"""
    command = {
        'module': 'file',
        'operation': 'read',
        'args': {'filename': filename}
    }
    
    result = openclaw.execute(command)
    
    if result['success']:
        console.print(Panel(
            result['content'],
            title=f"📄 {result['path']}",
            subtitle=f"{result['size']} characters",
            border_style="blue"
        ))
    else:
        console.print(f"[red]✗[/red] Error: {result['error']}")


@file.command()
@click.argument('filename')
@click.argument('content')
def write(filename, content):
    """Write content to file"""
    command = {
        'module': 'file',
        'operation': 'write',
        'args': {'filename': filename, 'content': content}
    }
    
    result = openclaw.execute(command)
    
    if result['success']:
        console.print(f"[green]✓[/green] Written: {result['path']}")
        console.print(f"  Size: {result['size']} bytes")
    else:
        console.print(f"[red]✗[/red] Error: {result['error']}")


@file.command()
@click.argument('filename')
@click.confirmation_option(prompt='Are you sure you want to delete this file?')
def delete(filename):
    """Delete a file (creates backup)"""
    command = {
        'module': 'file',
        'operation': 'delete',
        'args': {'filename': filename}
    }
    
    result = openclaw.execute(command)
    
    if result['success']:
        console.print(f"[yellow]🗑️[/yellow] Deleted: {result['path']}")
        console.print(f"  Backup: {result['backup']}")
    else:
        console.print(f"[red]✗[/red] Error: {result['error']}")


@file.command()
@click.argument('directory', default='.')
def list(directory):
    """List files in directory"""
    command = {
        'module': 'file',
        'operation': 'list_files',
        'args': {'directory': directory}
    }
    
    result = openclaw.execute(command)
    
    if result['success']:
        table = Table(title=f"📁 {result['path']}", show_header=True)
        table.add_column("Name", style="cyan")
        table.add_column("Type", style="magenta")
        table.add_column("Size", style="green")
        table.add_column("Modified", style="yellow")
        
        for item in result['files']:
            size = f"{item['size']} B" if item['size'] else "-"
            icon = "📁" if item['type'] == 'dir' else "📄"
            table.add_row(
                f"{icon} {item['name']}",
                item['type'],
                size,
                item['modified'][:19]  # Trim to datetime
            )
        
        console.print(table)
        console.print(f"\n[dim]Total: {result['count']} items[/dim]")
    else:
        console.print(f"[red]✗[/red] Error: {result['error']}")


@file.command()
@click.argument('filename')
def info(filename):
    """Get file information"""
    command = {
        'module': 'file',
        'operation': 'get_info',
        'args': {'filename': filename}
    }
    
    result = openclaw.execute(command)
    
    if result['success']:
        info_text = f"""[yellow]Path:[/yellow] {result['path']}
[yellow]Name:[/yellow] {result['name']}
[yellow]Size:[/yellow] {result['size']} bytes
[yellow]Type:[/yellow] {'Directory' if result['is_dir'] else 'File'}
[yellow]Created:[/yellow] {result['created']}
[yellow]Modified:[/yellow] {result['modified']}"""
        
        console.print(Panel(info_text, title="File Information", border_style="blue"))
    else:
        console.print(f"[red]✗[/red] Error: {result['error']}")


@cli.command()
def emergency_stop():
    """Activate emergency stop (blocks all operations)"""
    safety.activate_emergency_stop()
    console.print("[red]🚨 EMERGENCY STOP ACTIVATED[/red]")
    console.print("All operations are now blocked.")
    console.print("Use 'openclaw resume' to deactivate.")


@cli.command()
def resume():
    """Deactivate emergency stop"""
    safety.deactivate_emergency_stop()
    console.print("[green]✓ Emergency stop deactivated[/green]")
    console.print("Operations resumed.")


@cli.command()
@click.argument('natural_language', nargs=-1, required=True)
def ai(natural_language):
    """
    Execute command using AI natural language parsing
    
    Example:
        openclaw ai create a test file with hello world
        openclaw ai list all files in workspace
        openclaw ai delete old backup files
    """
    # Join multi-word input
    user_input = ' '.join(natural_language)
    
    # Create AI handler
    workspace = Path(openclaw.modules['file'].workspace)
    handler = create_ai_handler(workspace)
    
    # Check if AI is available
    if not handler.check_availability():
        console.print("[red]✗[/red] AI parsing not available")
        console.print("  Make sure Ollama is running with llama3.2 model")
        console.print("  Run: ollama pull llama3.2")
        return
    
    console.print(f"[dim]🤖 Parsing: '{user_input}'...[/dim]")
    
    # Parse and validate through full safety pipeline
    result = handler.parse_and_validate(user_input)
    
    # Check if safe
    if not result['safe']:
        console.print(f"\n{result['error']}")
        return
    
    # Show approval prompt
    prompt = handler.format_approval_prompt(result)
    console.print(prompt, end='')
    
    # Get user confirmation
    approval = input().strip().lower()
    
    if approval not in ['y', 'yes']:
        console.print("\n[yellow]⚠️  Command cancelled by user[/yellow]")
        return
    
    # Execute command
    console.print("\n[dim]Executing...[/dim]")
    exec_result = openclaw.execute(result['command'])
    
    # Show result
    if exec_result['success']:
        console.print(f"[green]✓[/green] Success!")
        # Show operation-specific output
        if 'content' in exec_result:
            console.print(Panel(
                exec_result['content'],
                title=f"📄 {exec_result.get('path', '')}",
                border_style="blue"
            ))
        elif 'files' in exec_result:
            console.print(f"  Found {exec_result['count']} items")
        else:
            console.print(f"  {exec_result.get('path', '')}")
    else:
        console.print(f"[red]✗[/red] Error: {exec_result['error']}")



if __name__ == '__main__':
    cli()
