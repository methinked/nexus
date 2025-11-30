"""
Nexus Agent - Main FastAPI application.

The Agent runs on each Raspberry Pi node and handles:
- Registration with Core
- System metrics collection
- Job execution
- Remote terminal access
"""

import logging
from contextlib import asynccontextmanager
from datetime import datetime
from uuid import UUID

from fastapi import FastAPI

from nexus.shared import AgentConfig, HealthResponse

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Load configuration
config = AgentConfig()

# Application startup time
startup_time = datetime.utcnow()

# Node state (populated after registration)
node_id: UUID | None = None
api_token: str | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for startup and shutdown events.
    """
    global node_id, api_token

    # Startup
    logger.info("Starting Nexus Agent...")
    logger.info(f"Node name: {config.node_name}")
    logger.info(f"Core URL: {config.core_url}")
    logger.info(f"Environment: {config.env}")
    logger.info(f"Listening on {config.host}:{config.port}")

    # TODO: Attempt to register with Core on startup
    # TODO: If already registered, load node_id and api_token from local storage
    # TODO: Start metrics collection background task
    # TODO: Start heartbeat background task

    yield

    # Shutdown
    logger.info("Shutting down Nexus Agent...")
    # TODO: Stop background tasks
    # TODO: Send final metrics to Core
    # TODO: Update node status to offline


# Create FastAPI application
app = FastAPI(
    title="Nexus Agent",
    description="Agent server running on Raspberry Pi nodes",
    version="0.1.0",
    lifespan=lifespan,
)


# ============================================================================
# Root Endpoints
# ============================================================================


@app.get("/", tags=["root"])
async def root():
    """Root endpoint with basic information."""
    return {
        "name": "Nexus Agent",
        "version": "0.1.0",
        "node_name": config.node_name,
        "node_id": str(node_id) if node_id else None,
        "status": "registered" if node_id else "unregistered",
        "core_url": config.core_url,
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
        node_id=node_id,
    )


# ============================================================================
# API Routers
# ============================================================================

from nexus.agent.api import jobs, system

app.include_router(system.router, prefix="/api/system", tags=["system"])
app.include_router(jobs.router, prefix="/api/jobs", tags=["jobs"])


# ============================================================================
# Entry Point
# ============================================================================


def main():
    """Run the Agent server with uvicorn."""
    import uvicorn

    uvicorn.run(
        "nexus.agent.main:app",
        host=config.host,
        port=config.port,
        reload=config.env == "development",
        log_level=config.log_level.lower(),
    )


if __name__ == "__main__":
    main()
