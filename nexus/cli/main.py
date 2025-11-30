"""
Nexus CLI - Main entry point.

CLI-first interface for managing distributed Raspberry Pi fleets.
"""

import sys
from pathlib import Path

import typer
from rich.console import Console
from rich.traceback import install as install_rich_traceback

from nexus.shared.config import CLIConfig

# Install rich traceback handler for better error messages
install_rich_traceback(show_locals=True)

# Create Typer app
app = typer.Typer(
    name="nexus",
    help="Distributed Raspberry Pi Management System",
    add_completion=True,
    rich_markup_mode="rich",
)

# Rich console for output
console = Console()

# Global config instance
config: CLIConfig = CLIConfig()


@app.callback()
def main(
    ctx: typer.Context,
    core_url: str = typer.Option(
        None,
        "--core-url",
        "-u",
        help="URL of the Core server (overrides config)",
        envvar="NEXUS_CORE_URL",
    ),
    api_token: str = typer.Option(
        None,
        "--token",
        "-t",
        help="API token for authentication (overrides config)",
        envvar="NEXUS_API_TOKEN",
    ),
    output_format: str = typer.Option(
        None,
        "--format",
        "-f",
        help="Output format: rich, json, plain",
    ),
) -> None:
    """
    Nexus - Distributed Raspberry Pi Management System.

    Control your fleet from the command line.
    """
    global config

    # Override config with CLI options if provided
    if core_url:
        config.core_url = core_url
    if api_token:
        config.api_token = api_token
    if output_format:
        config.output_format = output_format

    # Store config in context for subcommands
    ctx.obj = config


@app.command()
def version() -> None:
    """Show version information."""
    from nexus.shared.models import HealthResponse

    version_info = HealthResponse(status="installed", version="0.1.0")
    console.print(f"[bold cyan]Nexus CLI[/bold cyan] v{version_info.version}")
    console.print(f"Core URL: {config.core_url}")


@app.command()
def info() -> None:
    """Show CLI configuration information."""
    console.print("\n[bold cyan]Nexus CLI Configuration[/bold cyan]\n")
    console.print(f"  Core URL:      {config.core_url}")
    console.print(f"  API Token:     {'***' + config.api_token[-8:] if config.api_token else '[red]Not set[/red]'}")
    console.print(f"  Output Format: {config.output_format}")
    console.print(f"  Log Level:     {config.log_level}")
    console.print()


# Import and register command groups
# Note: These imports must come after app is defined
try:
    from nexus.cli.commands import config as config_commands
    from nexus.cli.commands import job as job_commands
    from nexus.cli.commands import node as node_commands

    app.add_typer(config_commands.app, name="config", help="Configuration management")
    app.add_typer(node_commands.app, name="node", help="Node management")
    app.add_typer(job_commands.app, name="job", help="Job management")
except ImportError as e:
    # Commands not yet implemented - gracefully continue
    console.print(f"[yellow]Warning: Some command modules not yet available: {e}[/yellow]")


if __name__ == "__main__":
    app()
