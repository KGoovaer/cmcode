"""CLI interface for cmcode."""

import sys
from pathlib import Path

import click
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.live import Live
from rich.text import Text
from rich.status import Status
from rich.align import Align

from . import __version__
from .config import Config, get_default_config_template
from .core import ChatSession
from .tools import ToolExecutor


console = Console()
error_console = Console(stderr=True)

# ASCII art robot
ROBOT_ART = """
[bold blue]        ╔═══════════════╗
        ║  [white]┌─────────┐[/white]  ║
        ║  [white]│ ◉     ◉ │[/white]  ║
        ║  [white]│  ═════  │[/white]  ║
        ║  [white]└─────────┘[/white]  ║
        ║    [yellow]┌─────┐[/yellow]    ║
        ║    [yellow]│░░░░░│[/yellow]    ║
        ║    [yellow]└──┬──┘[/yellow]    ║
        ║   [magenta]┌─┘   └─┐[/magenta]   ║
        ╚═══════════════╝[/bold blue]

[bold cyan]             CMCODE[/bold cyan]
[dim]  AI assistant with tool-calling superpowers[/dim]
"""


def print_tool_call(tool_name: str, arguments: str, verbose: int) -> None:
    """Print tool call information based on verbosity."""
    if verbose >= 1:
        console.print(f"[dim][Tool: {tool_name}][/dim]")
    if verbose >= 2:
        console.print(f"[dim]  Args: {arguments}[/dim]")


def run_interactive(session: ChatSession, config: Config) -> int:
    """Run interactive chat mode."""
    # Show robot ASCII art banner
    console.print(ROBOT_ART)
    console.print(Panel(
        "[bold]Commands:[/bold] [dim]'exit' to quit • '/reset' to clear • '/help' for more[/dim]",
        border_style="blue",
        padding=(0, 2)
    ))
    console.print()
    
    while True:
        try:
            user_input = console.input("[bold green]You:[/bold green] ")
        except (EOFError, KeyboardInterrupt):
            console.print("\n[dim]Goodbye![/dim]")
            return 0
        
        user_input = user_input.strip()
        
        if not user_input:
            continue
        
        if user_input.lower() in ("exit", "quit"):
            console.print("[dim]Goodbye![/dim]")
            return 0
        
        if user_input.lower() == "/reset":
            session.reset()
            console.print("[dim]Conversation reset.[/dim]\n")
            continue
        
        if user_input.lower() == "/help":
            console.print("""
[bold]Commands:[/bold]
  exit, quit  - End the chat session
  /reset      - Clear conversation history
  /help       - Show this help message
""")
            continue
        
        console.print()
        
        try:
            if config.streaming and config.output_format == "rich":
                # Show thinking spinner until first chunk arrives
                response_text = ""
                first_chunk = True
                stream_gen = session.chat_stream(user_input)
                
                with console.status("[bold cyan]Processing...[/bold cyan]", spinner="dots") as status:
                    for chunk in stream_gen:
                        if first_chunk:
                            status.stop()
                            console.print("[bold blue]Assistant:[/bold blue] ", end="")
                            first_chunk = False
                        console.print(chunk, end="")
                        response_text += chunk
                
                if first_chunk:
                    # No chunks received, just print empty response
                    console.print("[bold blue]Assistant:[/bold blue] [dim](no response)[/dim]")
                console.print("\n")
            elif config.streaming:
                # Streaming with plain output (with simple spinner)
                print("Processing...", end="\r", flush=True)
                first_chunk = True
                for chunk in session.chat_stream(user_input):
                    if first_chunk:
                        print("                ", end="\r")  # Clear spinner
                        print("Assistant: ", end="", flush=True)
                        first_chunk = False
                    print(chunk, end="", flush=True)
                print("\n")
            else:
                # Non-streaming with spinner
                with console.status("[bold cyan]Processing...[/bold cyan]", spinner="dots"):
                    response = session.chat(user_input)
                if config.output_format == "rich":
                    console.print("[bold blue]Assistant:[/bold blue]", Markdown(response))
                else:
                    print(f"Assistant: {response}")
                console.print()
                
        except Exception as e:
            error_console.print(f"[red]Error: {e}[/red]")
            if config.verbose >= 2:
                import traceback
                error_console.print(traceback.format_exc())
    
    return 0


def run_single_query(session: ChatSession, config: Config, query: str) -> int:
    """Run a single query and exit."""
    try:
        if config.streaming:
            first_chunk = True
            stream_gen = session.chat_stream(query)
            
            with console.status("[bold cyan]Processing...[/bold cyan]", spinner="dots") as status:
                for chunk in stream_gen:
                    if first_chunk:
                        status.stop()
                        first_chunk = False
                    print(chunk, end="", flush=True)
            print()
        else:
            with console.status("[bold cyan]Processing...[/bold cyan]", spinner="dots"):
                response = session.chat(query)
            print(response)
        return 0
    except Exception as e:
        error_console.print(f"[red]Error: {e}[/red]", highlight=False)
        return 1


@click.group(invoke_without_command=True)
@click.option("-q", "--query", help="Single query to run (non-interactive)")
@click.option("-i", "--interactive", is_flag=True, help="Force interactive mode")
@click.option("-m", "--model", help="Model to use (default: gpt-4o)")
@click.option("-e", "--endpoint", help="API endpoint URL")
@click.option("-c", "--config", "config_path", help="Path to config file")
@click.option("-v", "--verbose", count=True, help="Increase verbosity (-v, -vv)")
@click.option("--no-stream", is_flag=True, help="Disable streaming output")
@click.option("--plain", is_flag=True, help="Plain text output (no rich formatting)")
@click.option("--json", "json_output", is_flag=True, help="JSON output format")
@click.option("-y", "--yes", is_flag=True, help="Auto-confirm file operations")
@click.option("-w", "--workspace", help="Workspace directory for file operations")
@click.version_option(version=__version__)
@click.pass_context
def main(
    ctx,
    query: str | None,
    interactive: bool,
    model: str | None,
    endpoint: str | None,
    config_path: str | None,
    verbose: int,
    no_stream: bool,
    plain: bool,
    json_output: bool,
    yes: bool,
    workspace: str | None,
):
    """
    cmcode - Chat with LLMs with tool-calling capabilities.
    
    Run without arguments for interactive mode, or use -q for single queries.
    
    \b
    Examples:
      cmcode                           # Interactive mode
      cmcode -q "list files in src/"   # Single query
      echo "explain this" | cmcode     # Pipe input
      cmcode -q "read poem.txt" -y     # Auto-confirm file ops
    """
    # Handle subcommands
    if ctx.invoked_subcommand is not None:
        return
    
    # Load configuration
    from dotenv import load_dotenv
    load_dotenv()
    
    config = Config.load(config_path)
    
    # Apply CLI overrides
    if model:
        config.model = model
    if endpoint:
        config.endpoint = endpoint
    if verbose:
        config.verbose = verbose
    if no_stream:
        config.streaming = False
    if plain:
        config.output_format = "plain"
    if json_output:
        config.output_format = "json"
    if yes:
        config.auto_confirm = True
    if workspace:
        config.workspace_dir = workspace
    
    # Validate configuration
    errors = config.validate()
    if errors:
        for error in errors:
            error_console.print(f"[red]Configuration error:[/red] {error}")
        sys.exit(2)
    
    # Create tool executor with callback for verbose output
    tool_executor = ToolExecutor(
        workspace_dir=config.workspace_dir,
        auto_confirm=config.auto_confirm
    )
    
    # Create session
    session = ChatSession(
        config=config,
        tool_executor=tool_executor,
        on_tool_call=lambda name, args: print_tool_call(name, args, config.verbose)
    )
    
    # Determine mode
    if query:
        # Single query mode
        sys.exit(run_single_query(session, config, query))
    elif not sys.stdin.isatty() and not interactive:
        # Piped input mode
        piped_input = sys.stdin.read().strip()
        if piped_input:
            sys.exit(run_single_query(session, config, piped_input))
        else:
            error_console.print("[red]No input provided[/red]")
            sys.exit(1)
    else:
        # Interactive mode
        sys.exit(run_interactive(session, config))


@main.command()
def init():
    """Create a default configuration file."""
    config_path = Path.cwd() / ".cmcode.yaml"
    
    if config_path.exists():
        if not click.confirm(f"{config_path} already exists. Overwrite?"):
            console.print("[dim]Cancelled.[/dim]")
            return
    
    config_path.write_text(get_default_config_template())
    console.print(f"[green]Created {config_path}[/green]")
    console.print("[dim]Edit this file to customize cmcode settings.[/dim]")


@main.command()
def config():
    """Show current configuration."""
    from dotenv import load_dotenv
    load_dotenv()
    
    cfg = Config.load()
    
    console.print(Panel.fit("[bold]Current Configuration[/bold]", border_style="blue"))
    console.print(f"  Endpoint: {cfg.endpoint}")
    console.print(f"  Model: {cfg.model}")
    console.print(f"  API Key: {'[set]' if cfg.api_key else '[not set]'}")
    console.print(f"  Streaming: {cfg.streaming}")
    console.print(f"  Auto-confirm: {cfg.auto_confirm}")
    console.print(f"  Output format: {cfg.output_format}")
    console.print(f"  Workspace: {cfg.workspace_dir or '[current directory]'}")
    console.print()
    
    # Show config file locations
    console.print("[dim]Config file search paths:[/dim]")
    for path in Config.get_config_paths():
        exists = "[green]✓[/green]" if path.exists() else "[dim]✗[/dim]"
        console.print(f"  {exists} {path}")


if __name__ == "__main__":
    main()
