"""
Metrics API routes for Nexus Core.

Handles metrics submission from agents and historical queries.
"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from nexus.core.db import create_metric, get_metrics, get_node, update_node_status
from nexus.core.db.database import get_db
from nexus.shared import BaseResponse, Metric, MetricCreate, MetricList, NodeStatus

router = APIRouter()


@router.post("", response_model=BaseResponse, status_code=status.HTTP_201_CREATED)
async def submit_metrics(
    metric: MetricCreate,
    db: Session = Depends(get_db),
):
    """
    Submit metrics from agent.

    This endpoint is called by agents to push system metrics to Core.

    Args:
        metric: Metrics data from agent

    Returns:
        Acknowledgment response

    Raises:
        404: Node not found
    """
    # Validate that node exists
    node = get_node(db, str(metric.node_id))
    if not node:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Node {metric.node_id} not found",
        )

    # Store metrics in database
    create_metric(db, metric)

    # Update node status to ONLINE and last_seen timestamp
    update_node_status(
        db,
        str(metric.node_id),
        NodeStatus.ONLINE,
        datetime.utcnow(),
    )

    # TODO: Check for alerts/thresholds (Phase 3)

    return BaseResponse(message="Metrics received")


@router.get("/{node_id}", response_model=MetricList)
async def get_node_metrics(
    node_id: UUID,
    start_time: Optional[datetime] = Query(None, alias="since"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
):
    """
    Get historical metrics for a node.

    Query Parameters:
        since: Start timestamp (ISO format) - only metrics after this time
        skip: Number of metrics to skip (pagination)
        limit: Maximum number of metrics to return

    Args:
        node_id: UUID of the node

    Returns:
        List of metrics for the specified time range

    Raises:
        404: Node not found
    """
    # Validate node exists
    node = get_node(db, str(node_id))
    if not node:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Node {node_id} not found",
        )

    # Query database for metrics
    db_metrics = get_metrics(
        db,
        str(node_id),
        skip=skip,
        limit=limit,
        since=start_time,
    )

    # Convert to Pydantic models
    metrics = [Metric.model_validate(m) for m in db_metrics]

    # TODO: Implement aggregation by interval (Phase 3)

    return MetricList(node_id=node_id, metrics=metrics)
