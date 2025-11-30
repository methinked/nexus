"""
Metrics viewing commands.

Handles viewing and analyzing metrics data for nodes.
"""

from datetime import datetime, timedelta
from typing import Optional
from uuid import UUID

import httpx
import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from nexus.shared.config import CLIConfig

app = typer.Typer(help="View and analyze metrics")
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
        except Exception:
            return dt

    return dt.strftime("%Y-%m-%d %H:%M:%S")


def get_health_color(health: str) -> str:
    """Get color for health status."""
    colors = {
        "healthy": "green",
        "warning": "yellow",
        "critical": "red",
        "unknown": "dim",
    }
    return colors.get(health.lower(), "white")


@app.command("get")
def get_metrics(
    node_id: str = typer.Argument(..., help="Node ID to get metrics for"),
    limit: int = typer.Option(10, "--limit", "-n", help="Number of recent metrics to show"),
    since: Optional[str] = typer.Option(None, "--since", help="Start time (ISO format)"),
):
    """
    Get recent metrics for a node.

    Examples:
        nexus metrics get f6b858e2-1234-5678-abcd-123456789012
        nexus metrics get f6b858e2-1234-5678-abcd-123456789012 --limit 20
        nexus metrics get f6b858e2-1234-5678-abcd-123456789012 --since 2025-11-30T00:00:00
    """
    config = CLIConfig()

    try:
        # Build URL with query parameters
        params = {"limit": limit}
        if since:
            params["since"] = since

        # Fetch metrics from Core
        with httpx.Client(timeout=10.0) as client:
            response = client.get(
                f"{config.core_url}/api/metrics/{node_id}",
                headers=get_headers(config),
                params=params,
            )
            response.raise_for_status()
            data = response.json()

        metrics = data.get("metrics", [])

        if not metrics:
            console.print("[yellow]No metrics found for this node[/yellow]")
            raise typer.Exit(0)

        # Display metrics in a table
        table = Table(title=f"Recent Metrics for Node {node_id[:8]}...")

        table.add_column("Timestamp", style="cyan")
        table.add_column("CPU %", justify="right")
        table.add_column("Memory %", justify="right")
        table.add_column("Disk %", justify="right")
        table.add_column("Temp °C", justify="right")

        for metric in metrics:
            timestamp = format_datetime(metric.get("timestamp"))
            cpu = f"{metric.get('cpu_percent', 0):.1f}"
            memory = f"{metric.get('memory_percent', 0):.1f}"
            disk = f"{metric.get('disk_percent', 0):.1f}"
            temp = f"{metric.get('temperature', 0):.1f}" if metric.get('temperature') else "[dim]N/A[/dim]"

            # Color code high values
            cpu_display = f"[red]{cpu}[/red]" if float(cpu) >= 90 else cpu
            memory_display = f"[red]{memory}[/red]" if float(memory) >= 90 else memory
            disk_display = f"[red]{disk}[/red]" if float(disk) >= 90 else disk

            table.add_row(timestamp, cpu_display, memory_display, disk_display, temp)

        console.print(table)
        console.print(f"\n[dim]Showing {len(metrics)} metrics[/dim]")

    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            console.print(f"[red]Node {node_id} not found[/red]")
        else:
            console.print(f"[red]API error: {e.response.status_code} - {e.response.text}[/red]")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)


@app.command("stats")
def get_stats(
    node_id: str = typer.Argument(..., help="Node ID to get statistics for"),
    since: Optional[str] = typer.Option(None, "--since", help="Start time (ISO format)"),
    until: Optional[str] = typer.Option(None, "--until", help="End time (ISO format)"),
    hours: Optional[int] = typer.Option(None, "--hours", "-h", help="Last N hours"),
):
    """
    Get aggregated statistics for a node's metrics.

    Shows min, max, and average values over a time period.

    Examples:
        nexus metrics stats f6b858e2-1234-5678-abcd-123456789012
        nexus metrics stats f6b858e2-1234-5678-abcd-123456789012 --hours 24
        nexus metrics stats f6b858e2-1234-5678-abcd-123456789012 --since 2025-11-30T00:00:00
    """
    config = CLIConfig()

    try:
        # Build query parameters
        params = {}
        if hours:
            # Calculate since timestamp from hours ago
            since_dt = datetime.utcnow() - timedelta(hours=hours)
            params["since"] = since_dt.isoformat()
        elif since:
            params["since"] = since
        if until:
            params["until"] = until

        # Fetch stats from Core
        with httpx.Client(timeout=10.0) as client:
            response = client.get(
                f"{config.core_url}/api/metrics/{node_id}/stats",
                headers=get_headers(config),
                params=params,
            )
            response.raise_for_status()
            stats = response.json()

        # Display statistics in a formatted panel
        time_range = f"{format_datetime(stats.get('start_time'))} → {format_datetime(stats.get('end_time'))}"
        count = stats.get('count', 0)

        # CPU stats
        cpu_stats = f"""[cyan]CPU Usage:[/cyan]
  Min: {stats.get('cpu_min', 0):.1f}%
  Avg: {stats.get('cpu_avg', 0):.1f}%
  Max: {stats.get('cpu_max', 0):.1f}%"""

        # Memory stats
        memory_stats = f"""[cyan]Memory Usage:[/cyan]
  Min: {stats.get('memory_min', 0):.1f}%
  Avg: {stats.get('memory_avg', 0):.1f}%
  Max: {stats.get('memory_max', 0):.1f}%"""

        # Disk stats
        disk_stats = f"""[cyan]Disk Usage:[/cyan]
  Min: {stats.get('disk_min', 0):.1f}%
  Avg: {stats.get('disk_avg', 0):.1f}%
  Max: {stats.get('disk_max', 0):.1f}%"""

        # Temperature stats (optional)
        temp_stats = ""
        if stats.get('temperature_avg') is not None:
            temp_stats = f"""[cyan]Temperature:[/cyan]
  Min: {stats.get('temperature_min', 0):.1f}°C
  Avg: {stats.get('temperature_avg', 0):.1f}°C
  Max: {stats.get('temperature_max', 0):.1f}°C"""

        content = f"""[bold]Time Range:[/bold] {time_range}
[bold]Sample Count:[/bold] {count} metrics

{cpu_stats}

{memory_stats}

{disk_stats}"""

        if temp_stats:
            content += f"\n\n{temp_stats}"

        panel = Panel(
            content,
            title=f"[bold]Statistics for Node {node_id[:8]}...[/bold]",
            border_style="blue",
        )

        console.print(panel)

    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            error_data = e.response.json()
            console.print(f"[red]{error_data.get('detail', 'Not found')}[/red]")
        else:
            console.print(f"[red]API error: {e.response.status_code} - {e.response.text}[/red]")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)


@app.command("health")
def get_health(
    node_id: str = typer.Argument(..., help="Node ID to check health for"),
):
    """
    Get health status for a node.

    Shows overall health and per-component status based on latest metrics.

    Example:
        nexus metrics health f6b858e2-1234-5678-abcd-123456789012
    """
    config = CLIConfig()

    try:
        # Fetch health status from Core
        with httpx.Client(timeout=10.0) as client:
            response = client.get(
                f"{config.core_url}/api/nodes/{node_id}/health",
                headers=get_headers(config),
            )
            response.raise_for_status()
            health = response.json()

        overall_health = health.get("overall_health", "unknown")
        health_color = get_health_color(overall_health)

        # Build health display
        last_check = format_datetime(health.get("last_check"))

        cpu_health = health.get("cpu_health", "unknown")
        memory_health = health.get("memory_health", "unknown")
        disk_health = health.get("disk_health", "unknown")
        temp_health = health.get("temperature_health")

        cpu_color = get_health_color(cpu_health)
        memory_color = get_health_color(memory_health)
        disk_color = get_health_color(disk_health)

        content = f"""[bold]Overall Health:[/bold] [{health_color}]{overall_health.upper()}[/{health_color}]
[bold]Last Check:[/bold] {last_check}

[cyan]Component Health:[/cyan]
  CPU:     [{cpu_color}]{cpu_health.upper()}[/{cpu_color}]
  Memory:  [{memory_color}]{memory_health.upper()}[/{memory_color}]
  Disk:    [{disk_color}]{disk_health.upper()}[/{disk_color}]"""

        if temp_health:
            temp_color = get_health_color(temp_health)
            content += f"\n  Temp:    [{temp_color}]{temp_health.upper()}[/{temp_color}]"

        # Add latest metrics if available
        latest = health.get("latest_metrics")
        if latest:
            content += f"""

[cyan]Latest Values:[/cyan]
  CPU:     {latest.get('cpu_percent', 0):.1f}%
  Memory:  {latest.get('memory_percent', 0):.1f}%
  Disk:    {latest.get('disk_percent', 0):.1f}%"""
            if latest.get('temperature'):
                content += f"\n  Temp:    {latest.get('temperature', 0):.1f}°C"

        panel = Panel(
            content,
            title=f"[bold]Health Status for Node {node_id[:8]}...[/bold]",
            border_style=health_color,
        )

        console.print(panel)

    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            console.print(f"[red]Node {node_id} not found[/red]")
        else:
            console.print(f"[red]API error: {e.response.status_code} - {e.response.text}[/red]")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)
