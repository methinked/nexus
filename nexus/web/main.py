"""
Nexus Web Dashboard - Main Application.

Provides web UI routes for the dashboard.
"""

from pathlib import Path

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

# Setup paths
WEB_DIR = Path(__file__).parent
TEMPLATES_DIR = WEB_DIR / "templates"
STATIC_DIR = WEB_DIR / "static"

# Setup templating
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

# Create router
router = APIRouter()


@router.get("/", response_class=HTMLResponse)
async def dashboard_home(request: Request):
    """
    Dashboard home page - Fleet overview.

    Shows:
    - Stat cards (nodes, jobs, alerts, uptime)
    - Fleet topology
    - Metrics charts
    - Recent activity
    """
    return templates.TemplateResponse(
        "dashboard.html",
        {
            "request": request,
            "page_title": "Dashboard",
            "active_page": "dashboard"
        }
    )


@router.get("/nodes", response_class=HTMLResponse)
async def nodes_page(request: Request):
    """
    Nodes list page.

    Shows sortable table of all nodes with live status.
    """
    return templates.TemplateResponse(
        "nodes.html",
        {
            "request": request,
            "page_title": "Nodes",
            "active_page": "nodes"
        }
    )


@router.get("/jobs", response_class=HTMLResponse)
async def jobs_page(request: Request):
    """
    Jobs management page.

    Shows active and historical jobs.
    """
    return templates.TemplateResponse(
        "jobs.html",
        {
            "request": request,
            "page_title": "Jobs",
            "active_page": "jobs"
        }
    )


@router.get("/logs", response_class=HTMLResponse)
async def logs_page(request: Request):
    """
    Centralized logs page.

    Shows logs from all nodes with filtering.
    """
    return templates.TemplateResponse(
        "logs.html",
        {
            "request": request,
            "page_title": "Logs",
            "active_page": "logs"
        }
    )


@router.get("/services", response_class=HTMLResponse)
async def services_page(request: Request):
    """
    Docker Services page.

    Manage Docker service templates.
    """
    return templates.TemplateResponse(
        "services.html",
        {
            "request": request,
            "page_title": "Docker Services",
            "active_page": "services"
        }
    )


@router.get("/deployments", response_class=HTMLResponse)
async def deployments_page(request: Request):
    """
    Deployments page.

    Manage service deployments across the fleet.
    """
    return templates.TemplateResponse(
        "deployments.html",
        {
            "request": request,
            "page_title": "Deployments",
            "active_page": "deployments"
        }
    )


@router.get("/settings", response_class=HTMLResponse)
async def settings_page(request: Request):
    """
    Settings page.

    Dashboard configuration and system settings.
    """
    return templates.TemplateResponse(
        "settings.html",
        {
            "request": request,
            "page_title": "Settings",
            "active_page": "settings"
        }
    )


def mount_static(app):
    """Mount static files directory to the FastAPI app."""
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
