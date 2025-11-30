"""
Nexus Core - Main FastAPI application.

The Core server handles node registration, job scheduling, metrics aggregation,
and provides the central API for the CLI and web dashboard.
"""

import logging
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

    # TODO: Run database migrations (requires alembic command)
    # TODO: Start background tasks (cleanup, monitoring, etc.)

    yield

    # Shutdown
    logger.info("Shutting down Nexus Core...")
    # Database connections are closed automatically per-request
    # TODO: Stop background tasks


# Create FastAPI application
app = FastAPI(
    title="Nexus Core",
    description="Central management server for Nexus distributed Pi fleet",
    version="0.1.0",
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


@app.get("/", tags=["root"])
async def root():
    """Root endpoint with basic information."""
    return {
        "name": "Nexus Core",
        "version": "0.1.0",
        "status": "running",
        "docs": "/docs",
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
        version="0.1.0",
        uptime=uptime,
    )


# ============================================================================
# API Routers
# ============================================================================

from nexus.core.api import auth, jobs, logs, metrics, nodes, terminal

app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(nodes.router, prefix="/api/nodes", tags=["nodes"])
app.include_router(jobs.router, prefix="/api/jobs", tags=["jobs"])
app.include_router(metrics.router, prefix="/api/metrics", tags=["metrics"])
app.include_router(logs.router, prefix="/api/logs", tags=["logs"])
app.include_router(terminal.router, prefix="/api", tags=["terminal"])


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
