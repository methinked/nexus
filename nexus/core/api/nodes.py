"""
Nodes API routes for Nexus Core.

Handles node management, status, and queries.
"""

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

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
from nexus.shared import (
    JobStatus,
    MetricData,
    Node,
    NodeList,
    NodeStatus,
    NodeUpdate,
    NodeWithMetrics,
)

router = APIRouter()


@router.get("", response_model=NodeList)
async def list_nodes(
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

    # Convert to Pydantic models
    nodes = [Node.model_validate(node) for node in db_nodes]

    # TODO: Implement tag filtering if needed
    if tag:
        nodes = [n for n in nodes if tag in n.metadata.tags]
        total = len(nodes)

    return NodeList(nodes=nodes, total=total)


@router.get("/{node_id}", response_model=NodeWithMetrics)
async def get_node_details(
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

    # Build response
    node = Node.model_validate(db_node)
    return NodeWithMetrics(
        **node.model_dump(),
        current_metrics=current_metrics,
        active_jobs=active_jobs,
    )


@router.put("/{node_id}", response_model=Node)
async def update_node_metadata(
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

    return Node.model_validate(db_node)


@router.delete("/{node_id}", status_code=status.HTTP_204_NO_CONTENT)
async def deregister_node(
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
