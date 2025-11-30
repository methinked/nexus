"""
Metrics API routes for Nexus Core.

Handles metrics submission from agents and historical queries.
"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Query, status

from nexus.shared import BaseResponse, MetricCreate, MetricList

router = APIRouter()


@router.post("", response_model=BaseResponse, status_code=status.HTTP_201_CREATED)
async def submit_metrics(metric: MetricCreate):
    """
    Submit metrics from agent.

    This endpoint is called by agents to push system metrics to Core.

    Args:
        metric: Metrics data from agent

    Returns:
        Acknowledgment response

    TODO: Implement metric storage
    TODO: Update node last_seen timestamp
    TODO: Check for alerts/thresholds
    """
    # TODO: Store metrics in database
    # TODO: Update node status to ONLINE
    # TODO: Update last_seen timestamp

    return BaseResponse(message="Metrics received")


@router.get("/{node_id}", response_model=MetricList)
async def get_metrics(
    node_id: UUID,
    start_time: Optional[datetime] = Query(None),
    end_time: Optional[datetime] = Query(None),
    interval: Optional[str] = Query(None, regex="^(1m|5m|1h|1d)$"),
):
    """
    Get historical metrics for a node.

    Query Parameters:
        start_time: Start timestamp (ISO format)
        end_time: End timestamp (ISO format)
        interval: Aggregation interval (1m, 5m, 1h, 1d)

    Args:
        node_id: UUID of the node

    Returns:
        List of metrics for the specified time range

    TODO: Implement database query
    TODO: Implement time range filtering
    TODO: Implement aggregation by interval
    """
    # TODO: Query database for metrics
    # TODO: Filter by time range
    # TODO: Aggregate if interval specified

    return MetricList(node_id=node_id, metrics=[])
