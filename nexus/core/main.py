"""
Nexus Core - Main FastAPI application.

The Core server handles node registration, job scheduling, metrics aggregation,
and provides the central API for the CLI and web dashboard.
"""

import logging
import socket
from contextlib import asynccontextmanager
from datetime import datetime

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from nexus.shared import CoreConfig, HealthResponse

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

from nexus.shared.config import APP_VERSION

# Load configuration
config = CoreConfig()


# Application startup time
startup_time = datetime.utcnow()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for startup and shutdown events.
    """
    # Startup
    logger.info("Starting Nexus Core...")
    logger.info(f"Environment: {config.env}")
    logger.info(f"Log level: {config.log_level}")
    logger.info(f"Database: {config.database_url}")
    logger.info(f"Listening on {config.host}:{config.port}")

    # Initialize database
    from nexus.core.db import init_db
    logger.info("Initializing database...")
    init_db()
    logger.info("Database initialized successfully")

    # Start background services
    from nexus.core.services.log_cleanup import LogCleanupService
    from nexus.core.services.data_retention import DataRetentionService

    log_cleanup_service = LogCleanupService(config)
    await log_cleanup_service.start()

    data_retention_service = DataRetentionService(config)
    await data_retention_service.start()

    from nexus.core.services.alert_service import AlertService
    alert_service = AlertService(config)
    await alert_service.start()

    yield

    # Shutdown
    logger.info("Shutting down Nexus Core...")

    # Stop background services
    await log_cleanup_service.stop()
    await data_retention_service.stop()
    await alert_service.stop()

    # Database connections are closed automatically per-request


# Create FastAPI application
app = FastAPI(
    title="Nexus Core",
    description="Central management server for Nexus distributed Pi fleet",
    version=APP_VERSION,
    lifespan=lifespan,
)


# Add CORS middleware (configure for production)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if config.env == "development" else [],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================================
# Root Endpoints
# ============================================================================

# Note: Root "/" is now handled by the web dashboard
# Old JSON endpoint moved to /api/
@app.get("/api", tags=["root"])
async def api_root():
    """API root endpoint with basic information."""
    return {
        "name": "Nexus Core API",
        "version": APP_VERSION,
        "status": "running",
        "docs": "/docs",
        "dashboard": "/",
    }



@app.get("/health", response_model=HealthResponse, tags=["health"])
async def health_check():
    """
    Health check endpoint.

    No authentication required - used by Docker healthcheck and monitoring.
    """
    uptime = int((datetime.utcnow() - startup_time).total_seconds())

    return HealthResponse(
        status="healthy",
        version=APP_VERSION,
        uptime=uptime,
        hostname=socket.gethostname(),
    )



# ============================================================================
# API Routers
# ============================================================================

from nexus.core.api import auth, jobs, logs, metrics, nodes, terminal, websocket, update, alerts

app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(nodes.router, prefix="/api/nodes", tags=["nodes"])
app.include_router(jobs.router, prefix="/api/jobs", tags=["jobs"])
app.include_router(metrics.router, prefix="/api/metrics", tags=["metrics"])
app.include_router(logs.router, prefix="/api/logs", tags=["logs"])
app.include_router(terminal.router, prefix="/api", tags=["terminal"])
app.include_router(websocket.router, prefix="/api", tags=["websocket"])
app.include_router(update.router, prefix="/api/update", tags=["update"])
app.include_router(alerts.router, prefix="/api/alerts", tags=["alerts"])

# ============================================================================
# Web Dashboard
# ============================================================================

from nexus.web import main as web

# Mount static files
web.mount_static(app)

# Include web routes (no prefix - root path)
app.include_router(web.router, tags=["web"])


# ============================================================================
# Entry Point
# ============================================================================


def main():
    """Run the Core server with uvicorn."""
    import uvicorn

    uvicorn.run(
        "nexus.core.main:app",
        host=config.host,
        port=config.port,
        reload=config.env == "development",
        log_level=config.log_level.lower(),
    )


if __name__ == "__main__":
    main()
