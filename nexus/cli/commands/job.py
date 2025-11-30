"""
Job management commands.

Handles job submission, listing, and status tracking.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Optional

import httpx
import typer
from rich.console import Console
from rich.table import Table

from nexus.shared.config import CLIConfig
from nexus.shared.models import JobStatus, JobType

app = typer.Typer(help="Job management")
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
        return "[dim]N/A[/dim]"

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
    """Get color for job status."""
    colors = {
        "pending": "yellow",
        "running": "blue",
        "completed": "green",
        "failed": "red",
    }
    return colors.get(status.lower(), "white")


@app.command()
def submit(
    ctx: typer.Context,
    node_id: str = typer.Argument(..., help="Node ID to run the job on"),
    job_type: str = typer.Option(..., "--type", "-t", help="Job type: ocr, shell, sync"),
    file_path: Optional[str] = typer.Option(None, "--file", "-f", help="File path (for OCR jobs)"),
    command: Optional[str] = typer.Option(None, "--command", "-c", help="Command (for shell jobs)"),
    language: str = typer.Option("eng", "--language", "-l", help="OCR language (default: eng)"),
    timeout: Optional[int] = typer.Option(None, "--timeout", help="Job timeout in seconds"),
) -> None:
    """
    Submit a new job to a node.

    Different job types require different options:
    - OCR: requires --file
    - Shell: requires --command
    - Sync: no additional options
    """
    config: CLIConfig = ctx.obj or CLIConfig()

    # Validate job type
    try:
        job_type_enum = JobType(job_type.lower())
    except ValueError:
        console.print(f"[red]Error: Invalid job type '{job_type}'[/red]")
        console.print(f"Valid types: {', '.join([t.value for t in JobType])}")
        raise typer.Exit(1)

    # Build payload based on job type
    payload = {}
    if timeout:
        payload["timeout"] = timeout

    if job_type_enum == JobType.OCR:
        if not file_path:
            console.print("[red]Error: --file is required for OCR jobs[/red]")
            raise typer.Exit(1)
        payload["file_path"] = file_path
        payload["language"] = language
        payload["output_format"] = "markdown"

    elif job_type_enum == JobType.SHELL:
        if not command:
            console.print("[red]Error: --command is required for shell jobs[/red]")
            raise typer.Exit(1)
        payload["command"] = command

    # Create job request
    job_data = {
        "type": job_type_enum.value,
        "node_id": node_id,
        "payload": payload,
    }

    try:
        with console.status("[bold green]Submitting job..."):
            response = httpx.post(
                f"{config.core_url}/api/jobs",
                headers=get_headers(config),
                json=job_data,
                timeout=10.0,
            )
            response.raise_for_status()
            job = response.json()

        console.print(f"[green]✓[/green] Job submitted successfully")
        console.print(f"  Job ID: {job['id']}")
        console.print(f"  Type:   {job['type']}")
        console.print(f"  Status: {job['status']}")
        console.print(f"\nUse [bold]nexus job get {job['id']}[/bold] to check status")

    except httpx.HTTPStatusError as e:
        console.print(f"[red]Error: API returned {e.response.status_code}[/red]")
        if e.response.status_code == 404:
            console.print(f"Node '{node_id}' not found.")
        try:
            error_detail = e.response.json()
            console.print(f"Details: {error_detail}")
        except:
            pass
        raise typer.Exit(1)
    except httpx.ConnectError:
        console.print(f"[red]Error: Could not connect to Core server.[/red]")
        raise typer.Exit(1)


@app.command()
def list(
    ctx: typer.Context,
    node_id: Optional[str] = typer.Option(None, "--node", "-n", help="Filter by node ID"),
    status: Optional[str] = typer.Option(None, "--status", "-s", help="Filter by status"),
    job_type: Optional[str] = typer.Option(None, "--type", "-t", help="Filter by job type"),
    limit: int = typer.Option(50, "--limit", "-l", help="Maximum number of jobs to show"),
    format_output: Optional[str] = typer.Option(
        None,
        "--format",
        "-f",
        help="Output format: rich, json, plain",
    ),
) -> None:
    """
    List jobs in the system.

    Shows job status, type, and timing information.
    """
    config: CLIConfig = ctx.obj or CLIConfig()
    output_format = format_output or config.output_format

    # Build query parameters
    params = {"limit": limit}
    if node_id:
        params["node_id"] = node_id
    if status:
        params["status"] = status
    if job_type:
        params["type"] = job_type

    try:
        with console.status("[bold green]Fetching jobs..."):
            response = httpx.get(
                f"{config.core_url}/api/jobs",
                headers=get_headers(config),
                params=params,
                timeout=10.0,
            )
            response.raise_for_status()
            data = response.json()

    except httpx.ConnectError:
        console.print(f"[red]Error: Could not connect to Core server.[/red]")
        raise typer.Exit(1)
    except httpx.HTTPStatusError as e:
        console.print(f"[red]Error: API returned {e.response.status_code}[/red]")
        raise typer.Exit(1)

    jobs = data.get("jobs", [])

    # Output based on format
    if output_format == "json":
        console.print(json.dumps(data, indent=2, default=str))
        return

    if output_format == "plain":
        for job in jobs:
            console.print(f"{job['id']}\t{job['type']}\t{job['status']}\t{job['node_id']}")
        return

    # Rich table output (default)
    if not jobs:
        console.print("\n[yellow]No jobs found.[/yellow]")
        console.print("Use [bold]nexus job submit[/bold] to create a new job.\n")
        return

    table = Table(title=f"Jobs ({len(jobs)} total)", show_header=True)
    table.add_column("Type", style="cyan", no_wrap=True)
    table.add_column("Status", no_wrap=True)
    table.add_column("Node", style="white", no_wrap=True)
    table.add_column("Created", style="dim")
    table.add_column("ID", style="dim", no_wrap=True)

    for job in jobs:
        status_str = job["status"]
        status_color = get_status_color(status_str)
        created = format_datetime(job.get("created_at"))

        table.add_row(
            job["type"],
            f"[{status_color}]●[/{status_color}] {status_str}",
            str(job["node_id"])[:8] + "...",
            created,
            str(job["id"])[:8] + "...",
        )

    console.print()
    console.print(table)
    console.print()


@app.command()
def get(
    ctx: typer.Context,
    job_id: str = typer.Argument(..., help="Job ID"),
    format_output: Optional[str] = typer.Option(
        None,
        "--format",
        "-f",
        help="Output format: rich, json, plain",
    ),
) -> None:
    """
    Get detailed information about a specific job.

    Shows job status, payload, and result if completed.
    """
    config: CLIConfig = ctx.obj or CLIConfig()
    output_format = format_output or config.output_format

    try:
        with console.status(f"[bold green]Fetching job {job_id}..."):
            response = httpx.get(
                f"{config.core_url}/api/jobs/{job_id}",
                headers=get_headers(config),
                timeout=10.0,
            )
            response.raise_for_status()
            job = response.json()

    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            console.print(f"[red]Error: Job '{job_id}' not found.[/red]")
        else:
            console.print(f"[red]Error: API returned {e.response.status_code}[/red]")
        raise typer.Exit(1)
    except httpx.ConnectError:
        console.print(f"[red]Error: Could not connect to Core server.[/red]")
        raise typer.Exit(1)

    # Output based on format
    if output_format == "json":
        console.print(json.dumps(job, indent=2, default=str))
        return

    # Rich output (default)
    status_color = get_status_color(job["status"])

    console.print()
    console.print(f"[bold cyan]Job {job['id']}[/bold cyan]")
    console.print(f"  Type:       {job['type']}")
    console.print(f"  Status:     [{status_color}]{job['status']}[/{status_color}]")
    console.print(f"  Node:       {job['node_id']}")
    console.print(f"  Created:    {format_datetime(job.get('created_at'))}")

    if job.get("started_at"):
        console.print(f"  Started:    {format_datetime(job['started_at'])}")
    if job.get("completed_at"):
        console.print(f"  Completed:  {format_datetime(job['completed_at'])}")

    # Payload
    if job.get("payload"):
        console.print(f"\n  [bold]Payload:[/bold]")
        payload = job["payload"]
        for key, value in payload.items():
            console.print(f"    {key}: {value}")

    # Result
    if job.get("result"):
        result = job["result"]
        console.print(f"\n  [bold]Result:[/bold]")
        console.print(f"    Success: {result.get('success', False)}")
        if result.get("output"):
            console.print(f"    Output:  {result['output']}")
        if result.get("error"):
            console.print(f"    Error:   [red]{result['error']}[/red]")

    console.print()


@app.command()
def cancel(
    ctx: typer.Context,
    job_id: str = typer.Argument(..., help="Job ID to cancel"),
) -> None:
    """
    Cancel a running or pending job.

    (Not yet implemented - requires job cancellation support)
    """
    console.print("[yellow]Job cancellation is not yet implemented.[/yellow]")
    console.print("This feature will be available in a future phase.")
    raise typer.Exit(1)


@app.command()
def logs(
    ctx: typer.Context,
    job_id: str = typer.Argument(..., help="Job ID"),
    follow: bool = typer.Option(False, "--follow", "-f", help="Follow logs in real-time"),
) -> None:
    """
    View logs for a specific job.

    (Not yet implemented - requires logging infrastructure)
    """
    console.print("[yellow]Job logs are not yet implemented.[/yellow]")
    console.print("This feature will be available in Phase 4: The Brain")
    raise typer.Exit(1)
