"""
Nexus Agent - Main FastAPI application.

The Agent runs on each Raspberry Pi node and handles:
- Registration with Core
- System metrics collection
- Job execution
- Remote terminal access
"""

import json
import logging
import socket
from contextlib import asynccontextmanager
from datetime import datetime
from pathlib import Path
from uuid import UUID

import httpx
from fastapi import FastAPI

from nexus.agent.services.logging import LogCollector
from nexus.agent.services.metrics import MetricsCollector
from nexus.shared import AgentConfig, HealthResponse, NodeMetadata, RegistrationRequest

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
metrics_collector: MetricsCollector | None = None
log_collector: LogCollector | None = None
inventory_collector: "InventoryCollector | None" = None
job_queue: "JobQueue | None" = None
job_dispatcher: "JobDispatcher | None" = None

# Path to store registration data
STATE_FILE = config.data_dir / "agent_state.json"


def save_state():
    """Save node_id and api_token to local file."""
    if node_id and api_token:
        state = {
            "node_id": str(node_id),
            "api_token": api_token,
        }
        STATE_FILE.write_text(json.dumps(state, indent=2))
        logger.info(f"Agent state saved to {STATE_FILE}")


def load_state() -> tuple[UUID | None, str | None]:
    """Load node_id and api_token from local file."""
    if not STATE_FILE.exists():
        return None, None

    try:
        state = json.loads(STATE_FILE.read_text())
        loaded_node_id = UUID(state["node_id"])
        loaded_token = state["api_token"]
        logger.info(f"Loaded agent state from {STATE_FILE}")
        return loaded_node_id, loaded_token
    except Exception as e:
        logger.error(f"Failed to load agent state: {e}")
        return None, None


async def register_with_core(docker_storage_info: dict = None) -> tuple[UUID, str]:
    """
    Register this agent with the Core server.

    Args:
        docker_storage_info: Optional Docker storage metadata to include

    Returns:
        Tuple of (node_id, api_token)

    Raises:
        Exception if registration fails
    """
    # Get local IP address
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip_address = s.getsockname()[0]
        s.close()
    except Exception:
        ip_address = "127.0.0.1"

    # Build custom metadata
    custom_meta = {}
    if docker_storage_info:
        custom_meta["docker_storage"] = docker_storage_info

    # Create registration request
    registration = RegistrationRequest(
        name=config.node_name,
        ip_address=ip_address,
        shared_secret=config.shared_secret,
        metadata=NodeMetadata(
            location="",
            tags=[],
            description=f"Agent running on {config.node_name}",
            custom=custom_meta,
        ),
    )

    # Send registration request
    url = f"{config.core_url}/api/auth/register"
    async with httpx.AsyncClient() as client:
        response = await client.post(
            url,
            json=registration.model_dump(mode='json'),
            timeout=10.0,
        )
        response.raise_for_status()
        data = response.json()

    registered_node_id = UUID(data["node_id"])
    registered_token = data["api_token"]

    logger.info(f"Successfully registered with Core: node_id={registered_node_id}")
    return registered_node_id, registered_token


async def update_node_info(node_id: UUID, api_token: str):
    """
    Update node information (name) on Core.

    This ensures that if the agent configuration changes (e.g. name change),
    the Core is updated even if the node was already registered.
    """
    url = f"{config.core_url}/api/nodes/{node_id}"
    headers = {
        "Authorization": f"Bearer {api_token}",
    }

    # We only update the name for now
    payload = {
        "name": config.node_name
    }

    async with httpx.AsyncClient() as client:
        try:
            response = await client.put(
                url,
                json=payload,
                headers=headers,
                timeout=5.0,
            )
            response.raise_for_status()
            logger.info(f"Updated node info on Core: name={config.node_name}")
        except Exception as e:
            logger.warning(f"Failed to update node info: {e}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for startup and shutdown events.
    """
    global node_id, api_token, metrics_collector, log_collector, inventory_collector, job_queue, job_dispatcher

    # Startup
    logger.info("Starting Nexus Agent...")
    logger.info(f"Node name: {config.node_name}")
    logger.info(f"Core URL: {config.core_url}")
    logger.info(f"Environment: {config.env}")
    logger.info(f"Listening on {config.host}:{config.port}")

    # Setup Docker storage (if external storage available)
    logger.info("=" * 60)
    logger.info("DOCKER STORAGE CONFIGURATION")
    logger.info("=" * 60)

    from nexus.agent.services.storage import setup_docker_storage_if_needed, get_docker_root

    docker_disk = setup_docker_storage_if_needed()

    # Build storage metadata for Core
    docker_storage_info = None
    if docker_disk:
        logger.info(f"Docker configured for: {docker_disk.mount_point}")
        logger.info(f"  Type: {docker_disk.type.value}")
        logger.info(f"  Free space: {docker_disk.free_bytes / (1024**3):.1f} GB")

        if docker_disk.type.value == "sd_card":
            logger.warning("⚠️  Docker using SD card - consider adding external storage!")

        # Prepare metadata for Core
        docker_storage_info = {
            "docker_root": get_docker_root() or f"{docker_disk.mount_point}/docker",
            "storage_type": docker_disk.type.value,
            "storage_device": docker_disk.device,
            "storage_mount": docker_disk.mount_point,
            "storage_size_gb": round(docker_disk.total_bytes / (1024**3), 2),
            "storage_free_gb": round(docker_disk.free_bytes / (1024**3), 2),
            "storage_used_percent": docker_disk.usage_percent,
        }
    else:
        logger.warning("Could not determine Docker storage location")

    logger.info("=" * 60)

    # Try to load existing registration
    node_id, api_token = load_state()

    # If not registered, register with Core
    if not node_id or not api_token:
        logger.info("No existing registration found, registering with Core...")
        try:
            node_id, api_token = await register_with_core(docker_storage_info)
            save_state()
        except httpx.HTTPStatusError as e:
            logger.error(f"Registration failed: HTTP {e.response.status_code}")
            if e.response.status_code == 409:
                logger.error("Node with this name already registered. "
                           "Change NEXUS_NODE_NAME or delete existing node from Core.")
            raise
        except Exception as e:
            logger.error(f"Registration failed: {e}")
            raise
    else:
        logger.info(f"Using existing registration: node_id={node_id}")
        # Ensure Core has the latest name from specific config
        await update_node_info(node_id, api_token)

    # Start metrics collection
    metrics_collector = MetricsCollector(config, node_id, api_token)
    await metrics_collector.start()

    # Start log collection
    log_collector = LogCollector(config, node_id, api_token)
    await log_collector.start()

    # Start inventory collection (Phase 9 - Push Model)
    from nexus.agent.services.inventory import InventoryCollector
    inventory_collector = InventoryCollector(config, node_id, api_token)
    await inventory_collector.start()

    # Start job system
    from nexus.agent.services.job_queue import JobQueue
    from nexus.agent.services.job_dispatcher import JobDispatcher

    job_queue = JobQueue(max_concurrent=2)  # Limit to 2 concurrent jobs on Pi
    job_dispatcher = JobDispatcher(config, job_queue, str(node_id), api_token)
    await job_dispatcher.start()

    yield

    # Shutdown
    logger.info("Shutting down Nexus Agent...")

    # Stop job system
    if job_dispatcher:
        await job_dispatcher.stop()

    # Stop metrics collection
    if metrics_collector:
        await metrics_collector.stop()
    
    # Stop inventory collection
    if inventory_collector:
        await inventory_collector.stop()

    # Stop log collection
    if log_collector:
        await log_collector.stop()


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

from nexus.agent.api import docker, jobs, system, terminal

app.include_router(system.router, prefix="/api/system", tags=["system"])
app.include_router(jobs.router, prefix="/api/jobs", tags=["jobs"])
app.include_router(terminal.router, prefix="/api", tags=["terminal"])
app.include_router(docker.router, prefix="/api/docker", tags=["docker"])


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
