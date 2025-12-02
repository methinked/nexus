"""
Docker API routes for Nexus Agent.

Provides endpoints for Docker container management.
"""

import logging
from typing import Optional, Dict, Any, List
from uuid import UUID

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from nexus.agent.services.docker import DockerService

router = APIRouter()
logger = logging.getLogger(__name__)

# Initialize Docker service
docker_service = DockerService()


# Pydantic models
class DeploymentRequest(BaseModel):
    """Request to deploy a container."""
    deployment_id: str = Field(..., description="Deployment ID")
    image: str = Field(..., description="Docker image")
    name: Optional[str] = Field(None, description="Container name")
    ports: Optional[Dict[int, int]] = Field(None, description="Port mappings")
    volumes: Optional[Dict[str, Dict[str, str]]] = Field(None, description="Volume mappings")
    environment: Optional[Dict[str, str]] = Field(None, description="Environment variables")


class ContainerResponse(BaseModel):
    """Container information response."""
    id: str
    status: str
    message: Optional[str] = None


class ContainerStatusResponse(BaseModel):
    """Detailed container status."""
    id: str
    name: str
    status: str
    image: str
    created: str
    started_at: Optional[str]
    finished_at: Optional[str]
    exit_code: Optional[int]
    error: Optional[str]
    deployment_id: Optional[str]


@router.get("/status")
async def docker_status():
    """
    Check Docker availability.

    Returns Docker daemon status.
    """
    available = docker_service.is_available()

    return {
        "available": available,
        "message": "Docker is available" if available else "Docker is not available"
    }


@router.post("/deploy")
async def deploy_container(request: DeploymentRequest) -> ContainerResponse:
    """
    Deploy a new container.

    Creates and starts a Docker container based on deployment configuration.
    """
    if not docker_service.is_available():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Docker is not available on this agent"
        )

    try:
        # Prepare volume bindings in Docker format
        volumes_dict = None
        if request.volumes:
            volumes_dict = {
                host_path: {'bind': config['container'], 'mode': config.get('mode', 'rw')}
                for host_path, config in request.volumes.items()
            }

        # Create container
        container_id = docker_service.create_container(
            deployment_id=request.deployment_id,
            image=request.image,
            name=request.name,
            ports=request.ports,
            volumes=volumes_dict,
            environment=request.environment
        )

        if not container_id:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create container"
            )

        # Start container
        if not docker_service.start_container(container_id):
            # Clean up container if start fails
            docker_service.remove_container(container_id, force=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to start container"
            )

        return ContainerResponse(
            id=container_id,
            status="running",
            message="Container deployed successfully"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to deploy container: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Deployment failed: {str(e)}"
        )


@router.post("/{container_id}/start")
async def start_container(container_id: str) -> ContainerResponse:
    """Start a container."""
    if not docker_service.is_available():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Docker is not available"
        )

    success = docker_service.start_container(container_id)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Container {container_id} not found or failed to start"
        )

    return ContainerResponse(
        id=container_id,
        status="running",
        message="Container started successfully"
    )


@router.post("/{container_id}/stop")
async def stop_container(container_id: str) -> ContainerResponse:
    """Stop a container."""
    if not docker_service.is_available():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Docker is not available"
        )

    success = docker_service.stop_container(container_id)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Container {container_id} not found or failed to stop"
        )

    return ContainerResponse(
        id=container_id,
        status="stopped",
        message="Container stopped successfully"
    )


@router.post("/{container_id}/restart")
async def restart_container(container_id: str) -> ContainerResponse:
    """Restart a container."""
    if not docker_service.is_available():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Docker is not available"
        )

    success = docker_service.restart_container(container_id)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Container {container_id} not found or failed to restart"
        )

    return ContainerResponse(
        id=container_id,
        status="running",
        message="Container restarted successfully"
    )


@router.delete("/{container_id}")
async def remove_container(container_id: str, force: bool = False) -> ContainerResponse:
    """Remove a container."""
    if not docker_service.is_available():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Docker is not available"
        )

    success = docker_service.remove_container(container_id, force=force)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Container {container_id} not found or failed to remove"
        )

    return ContainerResponse(
        id=container_id,
        status="removed",
        message="Container removed successfully"
    )


@router.get("/{container_id}/status")
async def get_container_status(container_id: str) -> ContainerStatusResponse:
    """Get detailed container status."""
    if not docker_service.is_available():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Docker is not available"
        )

    status_info = docker_service.get_container_status(container_id)

    if not status_info:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Container {container_id} not found"
        )

    return ContainerStatusResponse(
        id=status_info['id'],
        name=status_info['name'],
        status=status_info['status'],
        image=status_info['image'],
        created=status_info['created'],
        started_at=status_info.get('started_at'),
        finished_at=status_info.get('finished_at'),
        exit_code=status_info.get('exit_code'),
        error=status_info.get('error'),
        deployment_id=status_info.get('labels', {}).get('nexus.deployment_id')
    )


@router.get("/{container_id}/logs")
async def get_container_logs(container_id: str, tail: int = 100):
    """Get container logs."""
    if not docker_service.is_available():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Docker is not available"
        )

    logs = docker_service.get_container_logs(container_id, tail=tail)

    if logs is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Container {container_id} not found"
        )

    return {
        "container_id": container_id,
        "logs": logs
    }


@router.get("/containers/list")
async def list_containers() -> List[Dict[str, Any]]:
    """List all Nexus-managed containers."""
    if not docker_service.is_available():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Docker is not available"
        )

    containers = docker_service.list_nexus_containers()

    return {
        "containers": containers,
        "total": len(containers)
    }
