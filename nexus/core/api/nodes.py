"""
Nodes API routes for Nexus Core.

Handles node management, status, and queries.
"""

from typing import Optional
from uuid import UUID

import logging
import httpx
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy.orm.attributes import flag_modified

from nexus.core.db import (
    delete_node,
    get_jobs_count,
    get_latest_metric,
    get_node,
    get_nodes,
    get_nodes_count,
    update_node as db_update_node,
)
from nexus.core.db.database import get_db
from nexus.core.services.health import calculate_node_health
from nexus.shared import (
    BaseResponse,
    DiskInfo,
    HealthThresholds,
    JobStatus,
    Metric,
    MetricData,
    Node,
    NodeHealthStatus,
    NodeList,
    NodeStatus,
    NodeUpdate,
    NodeWithMetrics,
    InventoryUpdate,
)

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("", response_model=NodeList)
def list_nodes(
    status_filter: Optional[NodeStatus] = Query(None, alias="status"),
    tag: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
):
    """
    List all registered nodes.

    Query Parameters:
        status: Filter by node status (online, offline, error)
        tag: Filter by metadata tag
        skip: Number of nodes to skip (pagination)
        limit: Maximum number of nodes to return

    Returns:
        List of nodes matching filters
    """
    # Get nodes from database
    db_nodes = get_nodes(db, skip=skip, limit=limit, status=status_filter)
    total = get_nodes_count(db, status=status_filter)

    # Convert to Pydantic models - map node_metadata to metadata
    nodes = []
    for db_node in db_nodes:
        node_dict = {
            "id": db_node.id,
            "name": db_node.name,
            "ip_address": db_node.ip_address,
            "status": db_node.status,
            "metadata": db_node.node_metadata,
            "created_at": db_node.created_at,
            "updated_at": db_node.updated_at,
            "last_seen": db_node.last_seen,
        }
        nodes.append(Node.model_validate(node_dict))

    # Filter by tag if provided
    if tag:
        nodes = [n for n in nodes if tag in n.metadata.tags]
        total = len(nodes)

    return NodeList(nodes=nodes, total=total)


@router.get("/{node_id}", response_model=NodeWithMetrics)
def get_node_details(
    node_id: UUID,
    db: Session = Depends(get_db),
):
    """
    Get detailed status of a specific node.

    Args:
        node_id: UUID of the node

    Returns:
        Node details with current metrics and active job count

    Raises:
        404: Node not found
    """
    # Query database for node
    db_node = get_node(db, str(node_id))
    if not db_node:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Node {node_id} not found",
        )

    # Get latest metrics
    latest_metric = get_latest_metric(db, str(node_id))
    current_metrics = None
    if latest_metric:
        current_metrics = MetricData(
            cpu_percent=latest_metric.cpu_percent,
            memory_percent=latest_metric.memory_percent,
            disk_percent=latest_metric.disk_percent,
            temperature=latest_metric.temperature,
        )

    # Count active jobs
    active_jobs = get_jobs_count(
        db,
        node_id=str(node_id),
        status=JobStatus.RUNNING,
    ) + get_jobs_count(
        db,
        node_id=str(node_id),
        status=JobStatus.PENDING,
    )

    # Build response - map node_metadata to metadata
    node_dict = {
        "id": db_node.id,
        "name": db_node.name,
        "ip_address": db_node.ip_address,
        "status": db_node.status,
        "metadata": db_node.node_metadata,
        "created_at": db_node.created_at,
        "updated_at": db_node.updated_at,
        "last_seen": db_node.last_seen,
    }
    node = Node.model_validate(node_dict)
    return NodeWithMetrics(
        **node.model_dump(),
        current_metrics=current_metrics,
        active_jobs=active_jobs,
    )


@router.put("/{node_id}", response_model=Node)
def update_node_metadata(
    node_id: UUID,
    update: NodeUpdate,
    db: Session = Depends(get_db),
):
    """
    Update node metadata.

    Args:
        node_id: UUID of the node
        update: Fields to update

    Returns:
        Updated node

    Raises:
        404: Node not found
    """
    # Update node in database
    db_node = db_update_node(db, str(node_id), update)
    if not db_node:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Node {node_id} not found",
        )

    # Map node_metadata to metadata
    node_dict = {
        "id": db_node.id,
        "name": db_node.name,
        "ip_address": db_node.ip_address,
        "status": db_node.status,
        "metadata": db_node.node_metadata,
        "created_at": db_node.created_at,
        "updated_at": db_node.updated_at,
        "last_seen": db_node.last_seen,
    }
    return Node.model_validate(node_dict)


@router.get("/{node_id}/health", response_model=NodeHealthStatus)
def get_node_health(
    node_id: UUID,
    db: Session = Depends(get_db),
    cpu_warning: float = Query(80.0, ge=0, le=100),
    cpu_critical: float = Query(95.0, ge=0, le=100),
    memory_warning: float = Query(85.0, ge=0, le=100),
    memory_critical: float = Query(95.0, ge=0, le=100),
    disk_warning: float = Query(85.0, ge=0, le=100),
    disk_critical: float = Query(95.0, ge=0, le=100),
    temperature_warning: Optional[float] = Query(75.0, ge=-50, le=150),
    temperature_critical: Optional[float] = Query(85.0, ge=-50, le=150),
):
    """
    Get health status for a node based on latest metrics.

    Calculates health status (HEALTHY, WARNING, CRITICAL, UNKNOWN) for each
    component (CPU, memory, disk, temperature) and overall health.

    Query Parameters (optional custom thresholds):
        cpu_warning: CPU usage % for warning (default: 80)
        cpu_critical: CPU usage % for critical (default: 95)
        memory_warning: Memory usage % for warning (default: 85)
        memory_critical: Memory usage % for critical (default: 95)
        disk_warning: Disk usage % for warning (default: 85)
        disk_critical: Disk usage % for critical (default: 95)
        temperature_warning: Temperature °C for warning (default: 75)
        temperature_critical: Temperature °C for critical (default: 85)

    Args:
        node_id: UUID of the node

    Returns:
        Health status with component breakdown and latest metrics

    Raises:
        404: Node not found
    """
    # Validate node exists
    db_node = get_node(db, str(node_id))
    if not db_node:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Node {node_id} not found",
        )

    # Get latest metric
    db_metric = get_latest_metric(db, str(node_id))

    # Convert to Pydantic model if exists
    latest_metric = Metric.model_validate(db_metric) if db_metric else None

    # Build custom thresholds
    thresholds = HealthThresholds(
        cpu_warning=cpu_warning,
        cpu_critical=cpu_critical,
        memory_warning=memory_warning,
        memory_critical=memory_critical,
        disk_warning=disk_warning,
        disk_critical=disk_critical,
        temperature_warning=temperature_warning,
        temperature_critical=temperature_critical,
    )

    # Calculate health status
    health_status = calculate_node_health(
        node_id=node_id,
        latest_metric=latest_metric,
        thresholds=thresholds,
    )

    return health_status


@router.post("/inventory", status_code=status.HTTP_200_OK)
def update_inventory(
    update: "InventoryUpdate",  # Quote to handle forward ref if needed, though imported
    db: Session = Depends(get_db),
):
    """
    Receive inventory update (disks, containers) from agent.
    
    This replaces the old "Pull" model. Agents push this data periodically.
    """
    logger.info(f"Received inventory update for node {update.node_id}. Disks: {len(update.disks)}, Containers: {len(update.containers)}")

    # Get node
    db_node = get_node(db, str(update.node_id))
    if not db_node:
        logger.error(f"Node {update.node_id} not found for inventory update")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Node {update.node_id} not found",
        )

    # Update metadata with inventory
    # We deliberately use a deep merge philosophy: keys not in update are preserved?
    # No, inventory is a snapshot. We overwrite the 'inventory' key.
    
    current_metadata = dict(db_node.node_metadata) if db_node.node_metadata else {} # Ensure dict
    # logger.info(f"Current metadata before update: {current_metadata.keys()}")
    
    current_metadata["inventory"] = {
        "disks": [d.model_dump(mode='json') for d in update.disks],
        "containers": update.containers,
        "updated_at": update.timestamp.isoformat()
    }
    
    # Save back to DB
    # Note: db_update_node might expect NodeUpdate model, or we can set directly
    db_node.node_metadata = current_metadata
    flag_modified(db_node, "node_metadata") # Force SQLAlchemy to detect JSON change
    
    try:
        db.commit()
        db.refresh(db_node)
        logger.info(f"Successfully saved inventory for {update.node_id}. Metadata keys: {db_node.node_metadata.keys()}")
    except Exception as e:
        logger.error(f"Failed to commit inventory update: {e}")
        db.rollback()
        raise e
    
    return BaseResponse(message="Inventory updated")


@router.get("/{node_id}/disks", response_model=list[DiskInfo])
def get_node_disks(
    node_id: UUID,
    db: Session = Depends(get_db),
):
    """
    Get disk information from a node (Cached).
    
    Reads from the last received inventory push.
    """
    db_node = get_node(db, str(node_id))
    if not db_node:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Node {node_id} not found",
        )

    inventory = db_node.node_metadata.get("inventory", {})
    disks_data = inventory.get("disks", [])
    
    return [DiskInfo.model_validate(d) for d in disks_data]


@router.get("/{node_id}/containers")
def get_node_containers(
    node_id: UUID,
    show_all: bool = Query(True),
    db: Session = Depends(get_db),
):
    """
    Get running containers from a node (Cached).
    
    Reads from the last received inventory push.
    """
    db_node = get_node(db, str(node_id))
    if not db_node:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Node {node_id} not found",
        )

    inventory = db_node.node_metadata.get("inventory", {})
    containers = inventory.get("containers", [])
    
    # If show_all is False, filter for nexus-managed? 
    # Current implementation of PUSH sends all. Filtering can happen here.
    # Logic: if 'managed' is true (though current container dict might not have it explicitly if raw docker list)
    # The agent inventory collector should ideally enrich this.
    # For now, return all.
    
    return {"containers": containers}


@router.delete("/{node_id}", status_code=status.HTTP_204_NO_CONTENT)
def deregister_node(
    node_id: UUID,
    db: Session = Depends(get_db),
):
    """
    Deregister a node.

    Args:
        node_id: UUID of the node

    Raises:
        404: Node not found

    Note:
        Associated jobs and metrics are automatically deleted via CASCADE
    """
    # Delete node from database
    success = delete_node(db, str(node_id))
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Node {node_id} not found",
        )

    return None
