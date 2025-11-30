"""
Node management commands.

Handles listing, viewing, and managing nodes in the fleet.
"""

import json
from datetime import datetime
from typing import Optional
from uuid import UUID

import httpx
import typer
from rich.console import Console
from rich.table import Table

from nexus.shared.config import CLIConfig
from nexus.shared.models import Node, NodeStatus

app = typer.Typer(help="Node management")
console = Console()


def get_headers(config: CLIConfig) -> dict:
    """Get HTTP headers with authentication if available."""
    headers = {"Content-Type": "application/json"}
    if config.api_token:
        headers["Authorization"] = f"Bearer {config.api_token}"
    return headers


def format_datetime(dt: Optional[datetime]) -> str:
    """Format datetime for display."""
    if not dt:
        return "[dim]Never[/dim]"

    # Handle string datetime from API
    if isinstance(dt, str):
        try:
            dt = datetime.fromisoformat(dt.replace('Z', '+00:00'))
        except:
            return dt

    # Calculate time ago
    now = datetime.utcnow()
    diff = now - dt

    if diff.total_seconds() < 60:
        return f"{int(diff.total_seconds())}s ago"
    elif diff.total_seconds() < 3600:
        return f"{int(diff.total_seconds() / 60)}m ago"
    elif diff.total_seconds() < 86400:
        return f"{int(diff.total_seconds() / 3600)}h ago"
    else:
        return f"{int(diff.total_seconds() / 86400)}d ago"


def get_status_color(status: str) -> str:
    """Get color for node status."""
    colors = {
        "online": "green",
        "offline": "red",
        "error": "yellow",
    }
    return colors.get(status.lower(), "white")


@app.command()
def list(
    ctx: typer.Context,
    status: Optional[str] = typer.Option(
        None,
        "--status",
        "-s",
        help="Filter by status: online, offline, error",
    ),
    format_output: Optional[str] = typer.Option(
        None,
        "--format",
        "-f",
        help="Output format: rich, json, plain",
    ),
) -> None:
    """
    List all nodes in the fleet.

    Shows node status, last seen time, and basic information.
    """
    config: CLIConfig = ctx.obj or CLIConfig()
    output_format = format_output or config.output_format

    # Build query parameters
    params = {}
    if status:
        params["status"] = status

    try:
        with console.status("[bold green]Fetching nodes..."):
            response = httpx.get(
                f"{config.core_url}/api/nodes",
                headers=get_headers(config),
                params=params,
                timeout=10.0,
            )
            response.raise_for_status()
            data = response.json()

    except httpx.ConnectError:
        console.print(f"[red]Error: Could not connect to Core server at {config.core_url}[/red]")
        console.print("Make sure the Core server is running.")
        raise typer.Exit(1)
    except httpx.HTTPStatusError as e:
        console.print(f"[red]Error: API returned {e.response.status_code}[/red]")
        if e.response.status_code == 401:
            console.print("Authentication failed. Check your API token.")
        raise typer.Exit(1)

    nodes = data.get("nodes", [])

    # Output based on format
    if output_format == "json":
        console.print(json.dumps(data, indent=2, default=str))
        return

    if output_format == "plain":
        for node in nodes:
            console.print(f"{node['id']}\t{node['name']}\t{node['status']}\t{node['ip_address']}")
        return

    # Rich table output (default)
    if not nodes:
        console.print("\n[yellow]No nodes found.[/yellow]")
        console.print("Use [bold]nexus node register[/bold] to add nodes to your fleet.\n")
        return

    table = Table(title=f"Nexus Fleet ({len(nodes)} nodes)", show_header=True)
    table.add_column("Name", style="cyan", no_wrap=True)
    table.add_column("Status", no_wrap=True)
    table.add_column("IP Address", style="white")
    table.add_column("Last Seen", style="dim")
    table.add_column("ID", style="dim", no_wrap=True)

    for node in nodes:
        status_str = node["status"]
        status_color = get_status_color(status_str)
        last_seen = format_datetime(node.get("last_seen"))

        table.add_row(
            node["name"],
            f"[{status_color}]●[/{status_color}] {status_str}",
            node["ip_address"],
            last_seen,
            str(node["id"])[:8] + "...",
        )

    console.print()
    console.print(table)
    console.print()


@app.command()
def get(
    ctx: typer.Context,
    node_id: str = typer.Argument(..., help="Node ID or name"),
    format_output: Optional[str] = typer.Option(
        None,
        "--format",
        "-f",
        help="Output format: rich, json, plain",
    ),
) -> None:
    """
    Get detailed information about a specific node.
    """
    config: CLIConfig = ctx.obj or CLIConfig()
    output_format = format_output or config.output_format

    try:
        with console.status(f"[bold green]Fetching node {node_id}..."):
            response = httpx.get(
                f"{config.core_url}/api/nodes/{node_id}",
                headers=get_headers(config),
                timeout=10.0,
            )
            response.raise_for_status()
            node = response.json()

    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            console.print(f"[red]Error: Node '{node_id}' not found.[/red]")
        else:
            console.print(f"[red]Error: API returned {e.response.status_code}[/red]")
        raise typer.Exit(1)
    except httpx.ConnectError:
        console.print(f"[red]Error: Could not connect to Core server.[/red]")
        raise typer.Exit(1)

    # Output based on format
    if output_format == "json":
        console.print(json.dumps(node, indent=2, default=str))
        return

    # Rich output (default)
    console.print()
    console.print(f"[bold cyan]{node['name']}[/bold cyan]")
    console.print(f"  ID:         {node['id']}")
    console.print(f"  Status:     [{get_status_color(node['status'])}]{node['status']}[/{get_status_color(node['status'])}]")
    console.print(f"  IP Address: {node['ip_address']}")
    console.print(f"  Last Seen:  {format_datetime(node.get('last_seen'))}")
    console.print(f"  Created:    {format_datetime(node.get('created_at'))}")

    # Metadata
    metadata = node.get("metadata", {})
    if metadata.get("location"):
        console.print(f"  Location:   {metadata['location']}")
    if metadata.get("description"):
        console.print(f"  Description: {metadata['description']}")
    if metadata.get("tags"):
        console.print(f"  Tags:       {', '.join(metadata['tags'])}")

    console.print()


@app.command()
def update(
    ctx: typer.Context,
    node_id: str = typer.Argument(..., help="Node ID or name"),
    name: Optional[str] = typer.Option(None, "--name", "-n", help="New node name"),
    location: Optional[str] = typer.Option(None, "--location", "-l", help="Node location"),
    description: Optional[str] = typer.Option(None, "--description", "-d", help="Node description"),
    tags: Optional[str] = typer.Option(None, "--tags", "-t", help="Comma-separated tags"),
) -> None:
    """
    Update node information.

    Allows updating node name, location, description, and tags.
    """
    config: CLIConfig = ctx.obj or CLIConfig()

    # Build update payload
    update_data = {}
    if name:
        update_data["name"] = name

    metadata = {}
    if location is not None:
        metadata["location"] = location
    if description is not None:
        metadata["description"] = description
    if tags is not None:
        metadata["tags"] = [tag.strip() for tag in tags.split(",")]

    if metadata:
        update_data["metadata"] = metadata

    if not update_data:
        console.print("[yellow]No update fields provided.[/yellow]")
        console.print("Use --name, --location, --description, or --tags to update node information.")
        raise typer.Exit(1)

    try:
        with console.status(f"[bold green]Updating node {node_id}..."):
            response = httpx.put(
                f"{config.core_url}/api/nodes/{node_id}",
                headers=get_headers(config),
                json=update_data,
                timeout=10.0,
            )
            response.raise_for_status()
            node = response.json()

        console.print(f"[green]✓[/green] Node updated successfully: {node['name']}")

    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            console.print(f"[red]Error: Node '{node_id}' not found.[/red]")
        else:
            console.print(f"[red]Error: API returned {e.response.status_code}[/red]")
        raise typer.Exit(1)


@app.command()
def delete(
    ctx: typer.Context,
    node_id: str = typer.Argument(..., help="Node ID or name"),
    force: bool = typer.Option(False, "--force", "-f", help="Skip confirmation"),
) -> None:
    """
    Deregister a node from the fleet.

    WARNING: This will remove the node from the database.
    """
    config: CLIConfig = ctx.obj or CLIConfig()

    if not force:
        from rich.prompt import Confirm

        if not Confirm.ask(f"Are you sure you want to delete node '{node_id}'?"):
            console.print("[yellow]Aborted.[/yellow]")
            raise typer.Exit(0)

    try:
        with console.status(f"[bold green]Deleting node {node_id}..."):
            response = httpx.delete(
                f"{config.core_url}/api/nodes/{node_id}",
                headers=get_headers(config),
                timeout=10.0,
            )
            response.raise_for_status()

        console.print(f"[green]✓[/green] Node deleted successfully")

    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            console.print(f"[red]Error: Node '{node_id}' not found.[/red]")
        else:
            console.print(f"[red]Error: API returned {e.response.status_code}[/red]")
        raise typer.Exit(1)


@app.command()
def shell(
    ctx: typer.Context,
    node_id: str = typer.Argument(..., help="Node ID or name"),
) -> None:
    """
    Open a remote shell to a node.

    (Not yet implemented - requires WebSocket support in Phase 4)
    """
    console.print("[yellow]Remote shell is not yet implemented.[/yellow]")
    console.print("This feature will be available in Phase 4: The Brain")
    console.print("\nFor now, you can SSH directly to the node's IP address.")
    raise typer.Exit(1)
