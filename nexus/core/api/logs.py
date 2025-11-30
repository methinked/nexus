"""
Logs API routes for Nexus Core.

Handles log submission from agents and log queries.
"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from nexus.core.db import create_log, get_logs, get_logs_count, get_node
from nexus.core.db.database import get_db
from nexus.shared import BaseResponse, LogCreate, LogEntry, LogLevel, LogList

router = APIRouter()


@router.post("", response_model=BaseResponse, status_code=status.HTTP_201_CREATED)
async def submit_log(
    log: LogCreate,
    db: Session = Depends(get_db),
):
    """
    Submit a log entry from agent.

    This endpoint is called by agents to push log entries to Core.

    Args:
        log: Log entry data from agent

    Returns:
        Acknowledgment response

    Raises:
        404: Node not found
    """
    # Validate that node exists
    node = get_node(db, str(log.node_id))
    if not node:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Node {log.node_id} not found",
        )

    # Store log in database
    create_log(db, log)

    return BaseResponse(message="Log received")


@router.get("/{node_id}", response_model=LogList)
async def get_node_logs(
    node_id: UUID,
    level: Optional[LogLevel] = Query(None, description="Filter by log level"),
    source: Optional[str] = Query(None, description="Filter by source (partial match)"),
    since: Optional[datetime] = Query(None, description="Start timestamp"),
    until: Optional[datetime] = Query(None, description="End timestamp"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
):
    """
    Get logs for a node.

    Query Parameters:
        level: Filter by log level (debug, info, warning, error, critical)
        source: Filter by source module (partial match)
        since: Start timestamp (ISO format)
        until: End timestamp (ISO format)
        skip: Number of logs to skip (pagination)
        limit: Maximum number of logs to return

    Args:
        node_id: UUID of the node

    Returns:
        List of logs matching filters

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

    # Query database for logs
    db_logs = get_logs(
        db,
        node_id=str(node_id),
        level=level.value if level else None,
        source=source,
        since=since,
        until=until,
        skip=skip,
        limit=limit,
    )

    # Get total count
    total = get_logs_count(
        db,
        node_id=str(node_id),
        level=level.value if level else None,
        source=source,
        since=since,
        until=until,
    )

    # Convert to Pydantic models
    logs = [LogEntry.model_validate(log) for log in db_logs]

    return LogList(logs=logs, total=total)


@router.get("", response_model=LogList)
async def get_all_logs(
    level: Optional[LogLevel] = Query(None, description="Filter by log level"),
    source: Optional[str] = Query(None, description="Filter by source (partial match)"),
    since: Optional[datetime] = Query(None, description="Start timestamp"),
    until: Optional[datetime] = Query(None, description="End timestamp"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
):
    """
    Get logs from all nodes.

    Query Parameters:
        level: Filter by log level (debug, info, warning, error, critical)
        source: Filter by source module (partial match)
        since: Start timestamp (ISO format)
        until: End timestamp (ISO format)
        skip: Number of logs to skip (pagination)
        limit: Maximum number of logs to return

    Returns:
        List of logs matching filters from all nodes
    """
    # Query database for logs (no node_id filter)
    db_logs = get_logs(
        db,
        node_id=None,
        level=level.value if level else None,
        source=source,
        since=since,
        until=until,
        skip=skip,
        limit=limit,
    )

    # Get total count
    total = get_logs_count(
        db,
        node_id=None,
        level=level.value if level else None,
        source=source,
        since=since,
        until=until,
    )

    # Convert to Pydantic models
    logs = [LogEntry.model_validate(log) for log in db_logs]

    return LogList(logs=logs, total=total)
