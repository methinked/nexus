"""
Log viewing commands.

Handles viewing and filtering logs from nodes.
"""

from datetime import datetime, timedelta
from typing import Optional

import httpx
import typer
from rich.console import Console
from rich.table import Table

from nexus.shared.config import CLIConfig

app = typer.Typer(help="View logs from nodes")
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


def get_level_color(level: str) -> str:
    """Get color for log level."""
    colors = {
        "debug": "dim",
        "info": "cyan",
        "warning": "yellow",
        "error": "red",
        "critical": "bold red",
    }
    return colors.get(level.lower(), "white")


@app.command("list")
def list_logs(
    node_id: Optional[str] = typer.Argument(None, help="Node ID to get logs for (optional - shows all if omitted)"),
    level: Optional[str] = typer.Option(None, "--level", "-l", help="Filter by log level (debug, info, warning, error, critical)"),
    source: Optional[str] = typer.Option(None, "--source", "-s", help="Filter by source (partial match)"),
    since: Optional[str] = typer.Option(None, "--since", help="Start time (ISO format)"),
    until: Optional[str] = typer.Option(None, "--until", help="End time (ISO format)"),
    hours: Optional[int] = typer.Option(None, "--hours", "-h", help="Last N hours"),
    limit: int = typer.Option(100, "--limit", "-n", help="Maximum number of logs to show"),
    follow: bool = typer.Option(False, "--follow", "-f", help="Follow logs in real-time (updates every 5 seconds)"),
):
    """
    View logs from nodes.

    Shows logs from all nodes or a specific node, with optional filtering.

    Examples:
        nexus logs list                                  # All logs from all nodes
        nexus logs list f6b858e2-1234                    # Logs from specific node
        nexus logs list --level error                    # Only error logs
        nexus logs list --source nexus.agent.main        # Logs from specific source
        nexus logs list --hours 24                       # Last 24 hours
        nexus logs list f6b858e2-1234 --follow           # Follow logs from node
    """
    config = CLIConfig()

    try:
        # Build query parameters
        params = {"limit": limit}

        if hours:
            # Calculate since timestamp from hours ago
            since_dt = datetime.utcnow() - timedelta(hours=hours)
            params["since"] = since_dt.isoformat()
        elif since:
            params["since"] = since

        if until:
            params["until"] = until
        if level:
            params["level"] = level
        if source:
            params["source"] = source

        # Build URL based on whether node_id is provided
        if node_id:
            url = f"{config.core_url}/api/logs/{node_id}"
            title = f"Logs for Node {node_id[:8]}..."
        else:
            url = f"{config.core_url}/api/logs"
            title = "Logs from All Nodes"

        # For follow mode, we need to track last seen timestamp
        last_timestamp = None

        while True:
            # If following, update since parameter to last timestamp
            if follow and last_timestamp:
                params["since"] = last_timestamp

            # Fetch logs from Core
            with httpx.Client(timeout=10.0) as client:
                response = client.get(
                    url,
                    headers=get_headers(config),
                    params=params,
                )
                response.raise_for_status()
                data = response.json()

            logs = data.get("logs", [])
            total = data.get("total", 0)

            if not logs:
                if not follow:
                    console.print("[yellow]No logs found matching the criteria[/yellow]")
                    raise typer.Exit(0)
            else:
                # Display logs in a table
                table = Table(title=title, show_header=True)

                if not node_id:
                    table.add_column("Node", style="magenta", max_width=12)
                table.add_column("Timestamp", style="cyan", max_width=19)
                table.add_column("Level", max_width=8)
                table.add_column("Source", style="blue", max_width=25)
                table.add_column("Message")

                for log in logs:
                    timestamp = format_datetime(log.get("timestamp"))
                    level_str = log.get("level", "info")
                    level_color = get_level_color(level_str)
                    level_display = f"[{level_color}]{level_str.upper()}[/{level_color}]"
                    source_str = log.get("source", "")
                    message = log.get("message", "")

                    # Update last timestamp for follow mode
                    if follow:
                        last_timestamp = log.get("timestamp")

                    if not node_id:
                        node_str = str(log.get("node_id", ""))[:8]
                        table.add_row(node_str, timestamp, level_display, source_str, message)
                    else:
                        table.add_row(timestamp, level_display, source_str, message)

                console.print(table)

                if not follow:
                    console.print(f"\n[dim]Showing {len(logs)} of {total} total logs[/dim]")
                    break

            # For follow mode, wait 5 seconds before next check
            if follow:
                import time
                time.sleep(5)
            else:
                break

    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            console.print(f"[red]Node {node_id} not found[/red]")
        else:
            console.print(f"[red]API error: {e.response.status_code} - {e.response.text}[/red]")
        raise typer.Exit(1)
    except KeyboardInterrupt:
        if follow:
            console.print("\n[dim]Stopped following logs[/dim]")
            raise typer.Exit(0)
        raise
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)


@app.command("tail")
def tail_logs(
    node_id: str = typer.Argument(..., help="Node ID to tail logs for"),
    lines: int = typer.Option(20, "--lines", "-n", help="Number of recent log lines to show"),
    follow: bool = typer.Option(False, "--follow", "-f", help="Follow logs in real-time"),
):
    """
    Tail recent logs from a node (like 'tail -f').

    Examples:
        nexus logs tail f6b858e2-1234                    # Last 20 logs
        nexus logs tail f6b858e2-1234 -n 50              # Last 50 logs
        nexus logs tail f6b858e2-1234 -f                 # Follow logs
    """
    # Use list command with specific parameters
    list_logs(node_id=node_id, limit=lines, follow=follow)


if __name__ == "__main__":
    app()
