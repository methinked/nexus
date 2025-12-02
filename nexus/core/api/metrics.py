"""
Metrics API routes for Nexus Core.

Handles metrics submission from agents and historical queries.
"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from nexus.core.db import (
    create_metric,
    get_metrics,
    get_metrics_stats,
    get_node,
    update_node_status,
)
from nexus.core.db.database import get_db
from nexus.shared import BaseResponse, Metric, MetricCreate, MetricList, MetricStats, NodeStatus

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
    db_metric = create_metric(db, metric)

    # Update node status to ONLINE and last_seen timestamp
    update_node_status(
        db,
        str(metric.node_id),
        NodeStatus.ONLINE,
        datetime.utcnow(),
    )

    # Broadcast metric update via WebSocket
    from nexus.core.services.websocket_manager import manager
    import asyncio
    asyncio.create_task(manager.broadcast_event("metric_update", {
        "node_id": str(metric.node_id),
        "timestamp": metric.timestamp.isoformat(),
        "cpu_percent": metric.cpu_percent,
        "memory_percent": metric.memory_percent,
        "disk_percent": metric.disk_percent,
        "temperature": metric.temperature,
    }))

    # Note: Health threshold checking is available via GET /api/nodes/{node_id}/health

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

    return MetricList(node_id=node_id, metrics=metrics)


@router.get("/{node_id}/stats", response_model=MetricStats)
async def get_node_metrics_stats(
    node_id: UUID,
    since: Optional[datetime] = Query(None, description="Start time for aggregation"),
    until: Optional[datetime] = Query(None, description="End time for aggregation"),
    db: Session = Depends(get_db),
):
    """
    Get aggregated statistics for node metrics over a time period.

    Returns min, max, and average values for all metric types.

    Query Parameters:
        since: Start timestamp (ISO format) - defaults to all time
        until: End timestamp (ISO format) - defaults to now

    Args:
        node_id: UUID of the node

    Returns:
        Aggregated statistics (min, max, avg) for CPU, memory, disk, temperature

    Raises:
        404: Node not found or no metrics available
    """
    # Validate node exists
    node = get_node(db, str(node_id))
    if not node:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Node {node_id} not found",
        )

    # Get aggregated statistics
    stats = get_metrics_stats(db, str(node_id), since=since, until=until)

    if not stats:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No metrics found for node {node_id} in the specified time range",
        )

    # Convert to Pydantic model
    return MetricStats(
        node_id=node_id,
        start_time=stats["start_time"],
        end_time=stats["end_time"],
        count=stats["count"],
        cpu_avg=stats["cpu_avg"],
        cpu_min=stats["cpu_min"],
        cpu_max=stats["cpu_max"],
        memory_avg=stats["memory_avg"],
        memory_min=stats["memory_min"],
        memory_max=stats["memory_max"],
        disk_avg=stats["disk_avg"],
        disk_min=stats["disk_min"],
        disk_max=stats["disk_max"],
        temperature_avg=stats["temperature_avg"],
        temperature_min=stats["temperature_min"],
        temperature_max=stats["temperature_max"],
    )
