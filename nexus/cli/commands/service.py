"""
Service template management commands.

Handles creation and management of Docker service templates.
"""

import json
from typing import Optional

import httpx
import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.prompt import Prompt, Confirm

from nexus.shared.config import CLIConfig

app = typer.Typer(help="Manage Docker service templates")
console = Console()


def get_headers(config: CLIConfig) -> dict:
    """Get HTTP headers with authentication if available."""
    headers = {"Content-Type": "application/json"}
    if config.api_token:
        headers["Authorization"] = f"Bearer {config.api_token}"
    return headers


@app.command("list")
def list_services():
    """
    List all service templates.

    Example:
        nexus service list
    """
    config = CLIConfig()

    try:
        with httpx.Client(timeout=10.0) as client:
            response = client.get(
                f"{config.core_url}/api/services",
                headers=get_headers(config),
            )
            response.raise_for_status()
            data = response.json()

        services = data.get("services", [])

        if not services:
            console.print("[yellow]No service templates found[/yellow]")
            console.print("\n[dim]Create a new template with:[/dim] nexus service create")
            raise typer.Exit(0)

        # Display services in a table
        table = Table(title="Service Templates")

        table.add_column("ID", style="cyan", no_wrap=True)
        table.add_column("Name", style="bold")
        table.add_column("Image")
        table.add_column("Description")

        for service in services:
            service_id = service.get("id", "")[:8]
            name = service.get("name", "")
            image = service.get("image", "")
            description = service.get("description", "")[:50]
            if len(service.get("description", "")) > 50:
                description += "..."

            table.add_row(service_id, name, image, description)

        console.print(table)
        console.print(f"\n[dim]Total: {len(services)} templates[/dim]")

    except httpx.HTTPStatusError as e:
        console.print(f"[red]API error: {e.response.status_code} - {e.response.text}[/red]")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)


@app.command("get")
def get_service(
    service_id: str = typer.Argument(..., help="Service template ID"),
):
    """
    Get details of a service template.

    Example:
        nexus service get f6b858e2
    """
    config = CLIConfig()

    try:
        with httpx.Client(timeout=10.0) as client:
            response = client.get(
                f"{config.core_url}/api/services/{service_id}",
                headers=get_headers(config),
            )
            response.raise_for_status()
            service = response.json()

        # Format service details
        content = f"""[cyan]Name:[/cyan] {service.get('name', 'N/A')}
[cyan]Image:[/cyan] {service.get('image', 'N/A')}
[cyan]Description:[/cyan] {service.get('description', 'N/A')}

[cyan]Ports:[/cyan]"""

        ports = service.get('ports', [])
        if ports:
            for port in ports:
                protocol = port.get('protocol', 'tcp')
                content += f"\n  {port.get('host')}:{port.get('container')}/{protocol}"
        else:
            content += " None"

        content += "\n\n[cyan]Volumes:[/cyan]"
        volumes = service.get('volumes', [])
        if volumes:
            for vol in volumes:
                content += f"\n  {vol.get('host')} → {vol.get('container')}"
        else:
            content += " None"

        content += "\n\n[cyan]Environment:[/cyan]"
        env = service.get('environment', {})
        if env:
            for key, value in env.items():
                content += f"\n  {key}={value}"
        else:
            content += " None"

        content += f"\n\n[dim]Created: {service.get('created_at', 'N/A')}[/dim]"

        panel = Panel(
            content,
            title=f"[bold]Service Template: {service.get('name', 'N/A')}[/bold]",
            border_style="blue",
        )

        console.print(panel)

    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            console.print(f"[red]Service template {service_id} not found[/red]")
        else:
            console.print(f"[red]API error: {e.response.status_code} - {e.response.text}[/red]")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)


@app.command("create")
def create_service(
    name: str = typer.Option(..., "--name", "-n", help="Service name"),
    image: str = typer.Option(..., "--image", "-i", help="Docker image (e.g., nginx:latest)"),
    description: Optional[str] = typer.Option(None, "--description", "-d", help="Service description"),
    port: Optional[list[str]] = typer.Option(None, "--port", "-p", help="Port mapping (host:container or host:container/udp)"),
    volume: Optional[list[str]] = typer.Option(None, "--volume", "-v", help="Volume mapping (host:container)"),
    env: Optional[list[str]] = typer.Option(None, "--env", "-e", help="Environment variable (KEY=VALUE)"),
):
    """
    Create a new service template.

    Examples:
        nexus service create -n pihole -i pihole/pihole:latest -d "Network-wide ad blocking"
        nexus service create -n nginx -i nginx:latest -p 80:80 -v /data/nginx:/usr/share/nginx/html
        nexus service create -n app -i myapp:latest -e PORT=3000 -e DEBUG=true
    """
    config = CLIConfig()

    try:
        # Build service template data
        service_data = {
            "name": name,
            "image": image,
        }

        if description:
            service_data["description"] = description

        # Parse ports
        if port:
            ports = []
            for p in port:
                parts = p.split(":")
                if len(parts) != 2:
                    console.print(f"[red]Invalid port format: {p}. Use host:container or host:container/protocol[/red]")
                    raise typer.Exit(1)

                host_port = parts[0]
                container_part = parts[1]

                # Check for protocol
                protocol = "tcp"
                if "/" in container_part:
                    container_port, protocol = container_part.split("/")
                else:
                    container_port = container_part

                ports.append({
                    "host": int(host_port),
                    "container": int(container_port),
                    "protocol": protocol
                })
            service_data["ports"] = ports

        # Parse volumes
        if volume:
            volumes = []
            for v in volume:
                parts = v.split(":")
                if len(parts) != 2:
                    console.print(f"[red]Invalid volume format: {v}. Use host:container[/red]")
                    raise typer.Exit(1)
                volumes.append({
                    "host": parts[0],
                    "container": parts[1]
                })
            service_data["volumes"] = volumes

        # Parse environment variables
        if env:
            environment = {}
            for e in env:
                if "=" not in e:
                    console.print(f"[red]Invalid environment format: {e}. Use KEY=VALUE[/red]")
                    raise typer.Exit(1)
                key, value = e.split("=", 1)
                environment[key] = value
            service_data["environment"] = environment

        # Create service template
        with httpx.Client(timeout=10.0) as client:
            response = client.post(
                f"{config.core_url}/api/services",
                headers=get_headers(config),
                json=service_data,
            )
            response.raise_for_status()
            result = response.json()

        console.print(f"[green]✓[/green] Service template '{name}' created successfully")
        console.print(f"[dim]Service ID: {result.get('id')}[/dim]")
        console.print(f"\n[dim]View details with:[/dim] nexus service get {result.get('id')[:8]}")
        console.print(f"[dim]Deploy with:[/dim] nexus deployment create {result.get('id')[:8]} <node_id>")

    except httpx.HTTPStatusError as e:
        console.print(f"[red]API error: {e.response.status_code} - {e.response.text}[/red]")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)


@app.command("delete")
def delete_service(
    service_id: str = typer.Argument(..., help="Service template ID"),
    yes: bool = typer.Option(False, "--yes", "-y", help="Skip confirmation"),
):
    """
    Delete a service template.

    Example:
        nexus service delete f6b858e2
        nexus service delete f6b858e2 --yes
    """
    config = CLIConfig()

    # Confirm deletion
    if not yes:
        confirm = Confirm.ask(f"Are you sure you want to delete service template {service_id}?")
        if not confirm:
            console.print("[yellow]Cancelled[/yellow]")
            raise typer.Exit(0)

    try:
        with httpx.Client(timeout=10.0) as client:
            response = client.delete(
                f"{config.core_url}/api/services/{service_id}",
                headers=get_headers(config),
            )
            response.raise_for_status()

        console.print(f"[green]✓[/green] Service template {service_id} deleted successfully")

    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            console.print(f"[red]Service template {service_id} not found[/red]")
        else:
            console.print(f"[red]API error: {e.response.status_code} - {e.response.text}[/red]")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)
