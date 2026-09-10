"""
User management commands.

Allows creating and managing Nexus users via CLI.
"""

import json

import httpx
import typer
from rich.console import Console
from rich.table import Table

from nexus.shared.config import CLIConfig

app = typer.Typer(help="User management")
console = Console()


def get_headers(config: CLIConfig) -> dict:
    """Get HTTP headers with authentication if available."""
    headers = {"Content-Type": "application/json"}
    if config.api_token:
        headers["Authorization"] = f"Bearer {config.api_token}"
    return headers


@app.command()
def create(
    ctx: typer.Context,
    username: str = typer.Argument(..., help="Username for the new user"),
    role: str = typer.Option("viewer", "--role", "-r", help="Role (admin or viewer)"),
    password: str = typer.Option(..., "--password", "-p", prompt=True, hide_input=True, help="Password"),
) -> None:
    """
    Create a new user.
    Requires an API token with Admin privileges.
    """
    config: CLIConfig = ctx.obj or CLIConfig()

    payload = {
        "username": username,
        "password": password,
        "role": role.lower()
    }

    try:
        with console.status(f"[bold green]Creating user '{username}'..."):
            with httpx.Client(verify=False) as client:
                response = client.post(
                    f"{config.core_url}/api/users",
                    headers=get_headers(config),
                    json=payload,
                    timeout=10.0,
                )
            response.raise_for_status()

        console.print(f"[green]✓[/green] User '{username}' created successfully as {role.lower()}")

    except httpx.ConnectError:
        console.print(f"[red]Error: Could not connect to Core server at {config.core_url}[/red]")
        raise typer.Exit(1)
    except httpx.HTTPStatusError as e:
        console.print(f"[red]Error: API returned {e.response.status_code}[/red]")
        try:
            detail = e.response.json().get("detail", "")
            if detail:
                console.print(f"Details: {detail}")
        except:
            pass
        raise typer.Exit(1)


@app.command()
def list(
    ctx: typer.Context,
    format_output: str | None = typer.Option(
        None,
        "--format",
        "-f",
        help="Output format: rich, json, plain",
    ),
) -> None:
    """
    List all users.
    Requires an API token with Admin privileges.
    """
    config: CLIConfig = ctx.obj or CLIConfig()
    output_format = format_output or config.output_format

    try:
        with console.status("[bold green]Fetching users..."):
            with httpx.Client(verify=False) as client:
                response = client.get(
                    f"{config.core_url}/api/users",
                    headers=get_headers(config),
                    timeout=10.0,
                )
            response.raise_for_status()
            users = response.json()

    except httpx.ConnectError:
        console.print(f"[red]Error: Could not connect to Core server at {config.core_url}[/red]")
        raise typer.Exit(1)
    except httpx.HTTPStatusError as e:
        console.print(f"[red]Error: API returned {e.response.status_code}[/red]")
        raise typer.Exit(1)

    if output_format == "json":
        console.print(json.dumps(users, indent=2))
        return

    if not users:
        console.print("\n[yellow]No users found.[/yellow]")
        return

    table = Table(title=f"Nexus Users ({len(users)})", show_header=True)
    table.add_column("Username", style="cyan")
    table.add_column("Role", style="green")
    table.add_column("ID", style="dim")

    for u in users:
        role_col = "magenta" if u.get("role") == "admin" else "green"
        table.add_row(
            u.get("username", "unknown"),
            f"[{role_col}]{u.get('role', 'viewer')}[/{role_col}]",
            u.get("id", "none")[:8] + "...",
        )

    console.print()
    console.print(table)
    console.print()
