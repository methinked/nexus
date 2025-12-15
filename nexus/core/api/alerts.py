"""
Alerts API routes for Nexus Core.

Handles alert queries and management.
"""

from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from nexus.core.db import (
    get_active_alerts,
    get_active_alerts_count,
)
from nexus.core.db.database import get_db
from nexus.shared.models import Alert, AlertList

router = APIRouter()


@router.get("", response_model=AlertList)
async def list_alerts(
    node_id: Optional[UUID] = Query(None),
    db: Session = Depends(get_db),
):
    """
    List all active alerts.
    
    Args:
        node_id: Optional filter by node UUID
    """
    # Get alerts from DB
    db_alerts = get_active_alerts(db, node_id=str(node_id) if node_id else None)
    
    # Convert to Pydantic models
    alerts = [Alert.model_validate(a) for a in db_alerts]
    
    return AlertList(alerts=alerts, total=len(alerts))


@router.get("/count", response_model=dict)
async def count_alerts(
    node_id: Optional[UUID] = Query(None),
    db: Session = Depends(get_db),
):
    """
    Get count of active alerts.
    """
    count = get_active_alerts_count(db, node_id=str(node_id) if node_id else None)
    return {"count": count}
