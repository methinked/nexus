"""
Deployment management commands.

Handles deployment of services to nodes and lifecycle management.
"""

import json
from typing import Optional

import httpx
import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.prompt import Confirm

from nexus.shared.config import CLIConfig

app = typer.Typer(help="Manage service deployments")
console = Console()


def get_headers(config: CLIConfig) -> dict:
    """Get HTTP headers with authentication if available."""
    headers = {"Content-Type": "application/json"}
    if config.api_token:
        headers["Authorization"] = f"Bearer {config.api_token}"
    return headers


def get_status_color(status: str) -> str:
    """Get color for deployment status."""
    colors = {
        "running": "green",
        "stopped": "yellow",
        "pending": "blue",
        "failed": "red",
        "unknown": "dim",
    }
    return colors.get(status.lower(), "white")


@app.command("list")
def list_deployments(
    node: Optional[str] = typer.Option(None, "--node", "-n", help="Filter by node ID"),
    status: Optional[str] = typer.Option(None, "--status", "-s", help="Filter by status"),
):
    """
    List all deployments.

    Examples:
        nexus deployment list
        nexus deployment list --node f6b858e2
        nexus deployment list --status running
    """
    config = CLIConfig()

    try:
        params = {}
        if node:
            params["node_id"] = node
        if status:
            params["status"] = status

        with httpx.Client(timeout=10.0) as client:
            response = client.get(
                f"{config.core_url}/api/deployments",
                headers=get_headers(config),
                params=params,
            )
            response.raise_for_status()
            data = response.json()

        deployments = data.get("deployments", [])

        if not deployments:
            console.print("[yellow]No deployments found[/yellow]")
            console.print("\n[dim]Create a deployment with:[/dim] nexus deployment create <service_id> <node_id>")
            raise typer.Exit(0)

        # Display deployments in a table
        table = Table(title="Deployments")

        table.add_column("ID", style="cyan", no_wrap=True)
        table.add_column("Name", style="bold")
        table.add_column("Service ID")
        table.add_column("Node ID")
        table.add_column("Status")
        table.add_column("Created")

        for deployment in deployments:
            deployment_id = deployment.get("id", "")[:8]
            name = deployment.get("name", "N/A")
            service_id = deployment.get("service_id", "")[:8]
            node_id = deployment.get("node_id", "")[:8]
            dep_status = deployment.get("status", "unknown")
            created = deployment.get("created_at", "N/A")

            # Format creation time
            if created != "N/A":
                try:
                    from datetime import datetime
                    dt = datetime.fromisoformat(created.replace('Z', '+00:00'))
                    created = dt.strftime("%Y-%m-%d %H:%M")
                except Exception:
                    pass

            status_color = get_status_color(dep_status)
            status_display = f"[{status_color}]{dep_status.upper()}[/{status_color}]"

            table.add_row(deployment_id, name, service_id, node_id, status_display, created)

        console.print(table)
        console.print(f"\n[dim]Total: {len(deployments)} deployments[/dim]")

    except httpx.HTTPStatusError as e:
        console.print(f"[red]API error: {e.response.status_code} - {e.response.text}[/red]")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)


@app.command("get")
def get_deployment(
    deployment_id: str = typer.Argument(..., help="Deployment ID"),
):
    """
    Get details of a deployment.

    Example:
        nexus deployment get f6b858e2
    """
    config = CLIConfig()

    try:
        with httpx.Client(timeout=10.0) as client:
            response = client.get(
                f"{config.core_url}/api/deployments/{deployment_id}",
                headers=get_headers(config),
            )
            response.raise_for_status()
            deployment = response.json()

        status = deployment.get('status', 'unknown')
        status_color = get_status_color(status)

        # Format deployment details
        content = f"""[cyan]Service:[/cyan] {deployment.get('service_name', 'N/A')}
[cyan]Node:[/cyan] {deployment.get('node_name', 'N/A')}
[cyan]Status:[/cyan] [{status_color}]{status.upper()}[/{status_color}]

[cyan]Configuration:[/cyan]"""

        config_data = deployment.get('config', {})

        # Show ports
        ports = config_data.get('ports', [])
        if ports:
            content += "\n  Ports:"
            for port in ports:
                protocol = port.get('protocol', 'tcp')
                content += f"\n    {port.get('host')}:{port.get('container')}/{protocol}"

        # Show volumes
        volumes = config_data.get('volumes', [])
        if volumes:
            content += "\n  Volumes:"
            for vol in volumes:
                content += f"\n    {vol.get('host')} → {vol.get('container')}"

        # Show environment
        env = config_data.get('environment', {})
        if env:
            content += "\n  Environment:"
            for key, value in env.items():
                content += f"\n    {key}={value}"

        content += f"\n\n[dim]Created: {deployment.get('created_at', 'N/A')}[/dim]"
        if deployment.get('started_at'):
            content += f"\n[dim]Started: {deployment.get('started_at')}[/dim]"

        panel = Panel(
            content,
            title=f"[bold]Deployment: {deployment.get('service_name', 'N/A')}[/bold]",
            border_style="blue",
        )

        console.print(panel)

    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            console.print(f"[red]Deployment {deployment_id} not found[/red]")
        else:
            console.print(f"[red]API error: {e.response.status_code} - {e.response.text}[/red]")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)


@app.command("create")
def create_deployment(
    service_id: str = typer.Argument(..., help="Service template ID"),
    node_id: str = typer.Argument(..., help="Target node ID"),
    name: Optional[str] = typer.Option(None, "--name", "-n", help="Deployment name"),
    env: Optional[list[str]] = typer.Option(None, "--env", "-e", help="Override environment variable (KEY=VALUE)"),
):
    """
    Create a new deployment.

    Deploys a service template to a specific node.

    Examples:
        nexus deployment create f6b858e2 a1b2c3d4 -n "My App"
        nexus deployment create f6b858e2 a1b2c3d4 -e PORT=8080 -e DEBUG=true
    """
    config = CLIConfig()

    try:
        # Build deployment data
        deployment_data = {
            "name": name or f"deployment-{service_id[:8]}",
            "service_id": service_id,
            "node_id": node_id,
        }

        # Parse environment variable overrides
        if env:
            environment = {}
            for e in env:
                if "=" not in e:
                    console.print(f"[red]Invalid environment format: {e}. Use KEY=VALUE[/red]")
                    raise typer.Exit(1)
                key, value = e.split("=", 1)
                environment[key] = value
            deployment_data["config"] = {"environment": environment}

        # Create deployment
        with httpx.Client(timeout=10.0) as client:
            response = client.post(
                f"{config.core_url}/api/deployments",
                headers=get_headers(config),
                json=deployment_data,
            )
            # Handle 422 specifically for UUID validation issues
            if response.status_code == 422:
                 console.print(f"[red]Validation Error: {response.text}[/red]")
                 console.print("[yellow]Tip: Ensure you are using FULL UUIDs for service_id and node_id[/yellow]")
                 raise typer.Exit(1)

            response.raise_for_status()
            result = response.json()

        console.print(f"[green]✓[/green] Deployment created successfully")
        console.print(f"[dim]Deployment ID: {result.get('id')}[/dim]")
        console.print(f"[dim]Status: {result.get('status')}[/dim]")
        console.print(f"\n[dim]View details with:[/dim] nexus deployment get {result.get('id')[:8]}")
        console.print(f"[dim]Start deployment with:[/dim] nexus deployment start {result.get('id')[:8]}")

    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            console.print(f"[red]Service or node not found[/red]")
        else:
            console.print(f"[red]API error: {e.response.status_code} - {e.response.text}[/red]")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)


@app.command("start")
def start_deployment(
    deployment_id: str = typer.Argument(..., help="Deployment ID"),
):
    """
    Start a deployment.

    Example:
        nexus deployment start f6b858e2
    """
    config = CLIConfig()

    try:
        with httpx.Client(timeout=10.0) as client:
            response = client.post(
                f"{config.core_url}/api/deployments/{deployment_id}/start",
                headers=get_headers(config),
            )
            response.raise_for_status()
            result = response.json()

        console.print(f"[green]✓[/green] Deployment started successfully")
        console.print(f"[dim]Status: {result.get('status')}[/dim]")

    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            console.print(f"[red]Deployment {deployment_id} not found[/red]")
        else:
            console.print(f"[red]API error: {e.response.status_code} - {e.response.text}[/red]")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)


@app.command("stop")
def stop_deployment(
    deployment_id: str = typer.Argument(..., help="Deployment ID"),
):
    """
    Stop a deployment.

    Example:
        nexus deployment stop f6b858e2
    """
    config = CLIConfig()

    try:
        with httpx.Client(timeout=10.0) as client:
            response = client.post(
                f"{config.core_url}/api/deployments/{deployment_id}/stop",
                headers=get_headers(config),
            )
            response.raise_for_status()
            result = response.json()

        console.print(f"[green]✓[/green] Deployment stopped successfully")
        console.print(f"[dim]Status: {result.get('status')}[/dim]")

    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            console.print(f"[red]Deployment {deployment_id} not found[/red]")
        else:
            console.print(f"[red]API error: {e.response.status_code} - {e.response.text}[/red]")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)


@app.command("restart")
def restart_deployment(
    deployment_id: str = typer.Argument(..., help="Deployment ID"),
):
    """
    Restart a deployment.

    Example:
        nexus deployment restart f6b858e2
    """
    config = CLIConfig()

    try:
        with httpx.Client(timeout=10.0) as client:
            response = client.post(
                f"{config.core_url}/api/deployments/{deployment_id}/restart",
                headers=get_headers(config),
            )
            response.raise_for_status()
            result = response.json()

        console.print(f"[green]✓[/green] Deployment restarted successfully")
        console.print(f"[dim]Status: {result.get('status')}[/dim]")

    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            console.print(f"[red]Deployment {deployment_id} not found[/red]")
        else:
            console.print(f"[red]API error: {e.response.status_code} - {e.response.text}[/red]")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)


@app.command("delete")
def delete_deployment(
    deployment_id: str = typer.Argument(..., help="Deployment ID"),
    yes: bool = typer.Option(False, "--yes", "-y", help="Skip confirmation"),
):
    """
    Delete a deployment (stops and removes).

    Examples:
        nexus deployment delete f6b858e2
        nexus deployment delete f6b858e2 --yes
    """
    config = CLIConfig()

    # Confirm deletion
    if not yes:
        confirm = Confirm.ask(f"Are you sure you want to delete deployment {deployment_id}?")
        if not confirm:
            console.print("[yellow]Cancelled[/yellow]")
            raise typer.Exit(0)

    try:
        with httpx.Client(timeout=10.0) as client:
            response = client.delete(
                f"{config.core_url}/api/deployments/{deployment_id}",
                headers=get_headers(config),
            )
            response.raise_for_status()

        console.print(f"[green]✓[/green] Deployment {deployment_id} deleted successfully")

    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            console.print(f"[red]Deployment {deployment_id} not found[/red]")
        else:
            console.print(f"[red]API error: {e.response.status_code} - {e.response.text}[/red]")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)
