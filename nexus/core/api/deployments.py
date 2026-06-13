"""
Deployments API routes for Nexus Core (Phase 7 - Docker Orchestration).

Handles Docker service deployment lifecycle management.
"""

import logging
from typing import Optional
from uuid import UUID

import httpx
import yaml
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from nexus.core.db import (
    create_deployment,
    delete_deployment,
    get_deployment,
    get_deployments,
    get_deployments_count,
    get_node,
    get_service,
    update_deployment,
    update_deployment_status,
)
from nexus.core.db.database import get_db
from nexus.shared import (
    Deployment,
    DeploymentCreate,
    DeploymentList,
    DeploymentStatus,
    DeploymentUpdate,
    NodeStatus,
)

router = APIRouter()
logger = logging.getLogger(__name__)


async def send_deploy_to_agent(node_ip: str, deployment_id: str, service_config: dict) -> Optional[str]:
    """
    Send deployment request to agent.

    Returns:
        Container ID if successful, None otherwise
    """
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"http://{node_ip}:8001/api/docker/deploy",
                json={
                    "deployment_id": deployment_id,
                    "image": service_config.get("image"),
                    "name": f"nexus-{deployment_id[:8]}",
                    "ports": service_config.get("ports"),
                    "volumes": service_config.get("volumes"),
                    "environment": service_config.get("environment")
                }
            )
            response.raise_for_status()
            data = response.json()
            return data.get("id")
    except Exception as e:
        logger.error(f"Failed to deploy to agent {node_ip}: {e}")
        return None


async def send_container_command(node_ip: str, container_id: str, command: str) -> bool:
    """
    Send container lifecycle command to agent.

    Args:
        node_ip: Agent IP address
        container_id: Docker container ID
        command: Command to execute (start, stop, restart)

    Returns:
        True if successful, False otherwise
    """
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.post(
                f"http://{node_ip}:8001/api/docker/{container_id}/{command}"
            )
            response.raise_for_status()
            return True
    except Exception as e:
        logger.error(f"Failed to {command} container on agent {node_ip}: {e}")
        return False


async def delete_container_on_agent(node_ip: str, container_id: str) -> bool:
    """
    Delete container on agent.

    Returns:
        True if successful, False otherwise
    """
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.delete(
                f"http://{node_ip}:8001/api/docker/{container_id}",
                params={"force": True}
            )
            response.raise_for_status()
            return True
    except Exception as e:
        logger.error(f"Failed to delete container on agent {node_ip}: {e}")
        return False


@router.get("", response_model=DeploymentList)
async def list_deployments(
    node_id: Optional[UUID] = Query(None, description="Filter by node"),
    service_id: Optional[UUID] = Query(None, description="Filter by service"),
    status_filter: Optional[DeploymentStatus] = Query(None, alias="status", description="Filter by status"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
):
    """
    List all deployments with optional filtering.

    - **node_id**: Filter deployments by node
    - **service_id**: Filter deployments by service template
    - **status**: Filter by deployment status (deploying, running, stopped, failed)
    - **skip**: Number of deployments to skip (pagination)
    - **limit**: Maximum number of deployments to return
    """
    deployments = get_deployments(
        db,
        skip=skip,
        limit=limit,
        node_id=str(node_id) if node_id else None,
        service_id=str(service_id) if service_id else None,
        status=status_filter,
    )
    total = get_deployments_count(
        db,
        node_id=str(node_id) if node_id else None,
        service_id=str(service_id) if service_id else None,
        status=status_filter,
    )

    return DeploymentList(
        deployments=[Deployment.model_validate(d) for d in deployments],
        total=total,
    )


@router.get("/{deployment_id}", response_model=Deployment)
async def get_deployment_details(
    deployment_id: UUID,
    db: Session = Depends(get_db),
):
    """
    Get detailed information about a specific deployment.

    - **deployment_id**: Deployment UUID
    """
    deployment = get_deployment(db, str(deployment_id))
    if not deployment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Deployment {deployment_id} not found",
        )

    return Deployment.model_validate(deployment)


@router.post("", response_model=Deployment, status_code=status.HTTP_201_CREATED)
async def create_new_deployment(
    deployment: DeploymentCreate,
    db: Session = Depends(get_db),
):
    """
    Create a new deployment of a service to a node.

    This will:
    1. Validate the service template exists
    2. Validate the target node exists and is online
    3. Create a deployment record with status DEPLOYING
    4. (Future) Send deployment job to the agent

    - **deployment**: Deployment configuration including service_id, node_id, and config
    """
    # Validate service exists
    service = get_service(db, str(deployment.service_id))
    if not service:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Service {deployment.service_id} not found",
        )

    # Validate node exists and is online
    node = get_node(db, str(deployment.node_id))
    if not node:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Node {deployment.node_id} not found",
        )

    if node.status != NodeStatus.ONLINE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Node {node.name} is {node.status.value}, must be online to deploy",
        )

    # Create deployment in pending status
    db_deployment = create_deployment(db, deployment)
    deployment_id = str(db_deployment.id)

    # Parse docker-compose YAML to extract service config
    try:
        compose_config = yaml.safe_load(service.docker_compose)
        # Get the first service from the compose file
        service_name = list(compose_config['services'].keys())[0]
        service_def = compose_config['services'][service_name]

        # Extract image
        image = service_def.get('image')

        # Parse ports (convert "80:80/tcp" to {80: 80})
        ports = {}
        if 'ports' in service_def:
            for port in service_def['ports']:
                if isinstance(port, str):
                    # Parse "host:container/protocol" or "host:container"
                    parts = port.split(':')
                    if len(parts) >= 2:
                        host_port = int(parts[0])
                        container_part = parts[1].split('/')[0]  # Remove /tcp, /udp
                        container_port = int(container_part)
                        ports[container_port] = host_port

        # Parse volumes (convert "./data:/var/lib" to volume bindings)
        volumes = {}
        if 'volumes' in service_def:
            for volume in service_def['volumes']:
                if isinstance(volume, str) and ':' in volume:
                    host_path, container_path = volume.split(':', 1)
                    # Convert relative paths to absolute paths
                    if host_path.startswith('./'):
                        # Use /opt/nexus/deployments/<deployment_id>/ as base
                        host_path = f"/opt/nexus/deployments/{deployment_id}/{host_path[2:]}"
                    volumes[host_path] = {'container': container_path, 'mode': 'rw'}

        # Get environment variables
        environment = service_def.get('environment', {})
        if isinstance(environment, list):
            # Convert list format to dict
            env_dict = {}
            for item in environment:
                if '=' in item:
                    key, value = item.split('=', 1)
                    env_dict[key] = value
            environment = env_dict

        # Merge with deployment config overrides
        if deployment.config:
            # deployment.config is a DeploymentConfig object, not a dict
            config_dict = deployment.config if isinstance(deployment.config, dict) else {}
        else:
            config_dict = {}

        service_config = {
            "image": image,
            "ports": config_dict.get("ports", ports),
            "volumes": config_dict.get("volumes", volumes),
            "environment": {
                **environment,
                **config_dict.get("environment", {})
            }
        }
    except Exception as e:
        logger.error(f"Failed to parse docker-compose YAML: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to parse service configuration: {str(e)}"
        )

    # Send deployment to agent
    container_id = await send_deploy_to_agent(node.ip_address, deployment_id, service_config)

    if container_id:
        # Update deployment with container_id and set status to running
        db_deployment.container_id = container_id
        update_deployment_status(db, deployment_id, DeploymentStatus.RUNNING)
        db.refresh(db_deployment)
    else:
        # Deployment failed
        update_deployment_status(db, deployment_id, DeploymentStatus.FAILED)
        db.refresh(db_deployment)

    return Deployment.model_validate(db_deployment)


@router.put("/{deployment_id}", response_model=Deployment)
async def update_deployment_config(
    deployment_id: UUID,
    deployment_update: DeploymentUpdate,
    db: Session = Depends(get_db),
):
    """
    Update a deployment's configuration.

    - **deployment_id**: Deployment UUID
    - **deployment_update**: Fields to update (partial update supported)
    """
    db_deployment = update_deployment(db, str(deployment_id), deployment_update)
    if not db_deployment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Deployment {deployment_id} not found",
        )

    return Deployment.model_validate(db_deployment)


@router.post("/{deployment_id}/start", response_model=Deployment)
async def start_deployment(
    deployment_id: UUID,
    db: Session = Depends(get_db),
):
    """
    Start a stopped deployment.

    - **deployment_id**: Deployment UUID
    """
    deployment = get_deployment(db, str(deployment_id))
    if not deployment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Deployment {deployment_id} not found",
        )

    if deployment.status == DeploymentStatus.RUNNING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Deployment is already running",
        )

    if not deployment.container_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Deployment has no container ID, cannot start",
        )

    # Get node to find IP address
    node = get_node(db, str(deployment.node_id))
    if not node:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Node not found",
        )

    # Send start command to agent
    success = await send_container_command(node.ip_address, deployment.container_id, "start")

    if success:
        db_deployment = update_deployment_status(db, str(deployment_id), DeploymentStatus.RUNNING)
    else:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to start container on agent",
        )

    return Deployment.model_validate(db_deployment)


@router.post("/{deployment_id}/stop", response_model=Deployment)
async def stop_deployment(
    deployment_id: UUID,
    db: Session = Depends(get_db),
):
    """
    Stop a running deployment.

    - **deployment_id**: Deployment UUID
    """
    deployment = get_deployment(db, str(deployment_id))
    if not deployment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Deployment {deployment_id} not found",
        )

    if deployment.status == DeploymentStatus.STOPPED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Deployment is already stopped",
        )

    if not deployment.container_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Deployment has no container ID, cannot stop",
        )

    # Get node to find IP address
    node = get_node(db, str(deployment.node_id))
    if not node:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Node not found",
        )

    # Send stop command to agent
    success = await send_container_command(node.ip_address, deployment.container_id, "stop")

    if success:
        db_deployment = update_deployment_status(db, str(deployment_id), DeploymentStatus.STOPPED)
    else:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to stop container on agent",
        )

    return Deployment.model_validate(db_deployment)


@router.post("/{deployment_id}/restart", response_model=Deployment)
async def restart_deployment(
    deployment_id: UUID,
    db: Session = Depends(get_db),
):
    """
    Restart a deployment (stop then start).

    - **deployment_id**: Deployment UUID
    """
    deployment = get_deployment(db, str(deployment_id))
    if not deployment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Deployment {deployment_id} not found",
        )

    if not deployment.container_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Deployment has no container ID, cannot restart",
        )

    # Get node to find IP address
    node = get_node(db, str(deployment.node_id))
    if not node:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Node not found",
        )

    # Send restart command to agent
    success = await send_container_command(node.ip_address, deployment.container_id, "restart")

    if success:
        db_deployment = update_deployment_status(db, str(deployment_id), DeploymentStatus.RUNNING)
    else:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to restart container on agent",
        )

    return Deployment.model_validate(db_deployment)


@router.delete("/{deployment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_deployment(
    deployment_id: UUID,
    db: Session = Depends(get_db),
):
    """
    Remove a deployment.

    This will:
    1. Stop the container on the agent (if running)
    2. Remove the container
    3. Delete the deployment record

    - **deployment_id**: Deployment UUID
    """
    deployment = get_deployment(db, str(deployment_id))
    if not deployment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Deployment {deployment_id} not found",
        )

    # Send remove command to agent if container exists
    if deployment.container_id:
        node = get_node(db, str(deployment.node_id))
        if node:
            # Attempt to delete container on agent (best effort)
            await delete_container_on_agent(node.ip_address, deployment.container_id)

    # Delete from database
    success = delete_deployment(db, str(deployment_id))
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete deployment",
        )
