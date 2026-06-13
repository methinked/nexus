"""
Services API routes for Nexus Core (Phase 7 - Docker Orchestration).

Handles Docker service template management.
"""

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from nexus.core.db import (
    create_service,
    delete_service,
    get_service,
    get_service_by_name,
    get_services,
    get_services_count,
    update_service,
)
from nexus.core.db.database import get_db
from nexus.shared import Service, ServiceCreate, ServiceList, ServiceUpdate

router = APIRouter()


@router.get("", response_model=ServiceList)
async def list_services(
    category: Optional[str] = Query(None, description="Filter by service category"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
):
    """
    List all service templates.

    - **category**: Optional category filter (networking, monitoring, automation, etc.)
    - **skip**: Number of services to skip (pagination)
    - **limit**: Maximum number of services to return
    """
    services = get_services(db, skip=skip, limit=limit, category=category)
    total = get_services_count(db, category=category)

    return ServiceList(
        services=[Service.model_validate(s) for s in services],
        total=total,
    )


@router.get("/{service_id}", response_model=Service)
async def get_service_details(
    service_id: UUID,
    db: Session = Depends(get_db),
):
    """
    Get detailed information about a specific service template.

    - **service_id**: Service UUID
    """
    service = get_service(db, str(service_id))
    if not service:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Service {service_id} not found",
        )

    return Service.model_validate(service)


@router.post("", response_model=Service, status_code=status.HTTP_201_CREATED)
async def create_service_template(
    service: ServiceCreate,
    db: Session = Depends(get_db),
):
    """
    Create a new service template.

    This endpoint is typically used by administrators to add custom service templates
    to the catalog.

    - **service**: Service template data including docker-compose YAML
    """
    # Check if service with same name already exists
    existing = get_service_by_name(db, service.name)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Service with name '{service.name}' already exists",
        )

    db_service = create_service(db, service)
    return Service.model_validate(db_service)


@router.put("/{service_id}", response_model=Service)
async def update_service_template(
    service_id: UUID,
    service_update: ServiceUpdate,
    db: Session = Depends(get_db),
):
    """
    Update an existing service template.

    - **service_id**: Service UUID
    - **service_update**: Fields to update (partial update supported)
    """
    db_service = update_service(db, str(service_id), service_update)
    if not db_service:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Service {service_id} not found",
        )

    return Service.model_validate(db_service)


@router.delete("/{service_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_service_template(
    service_id: UUID,
    db: Session = Depends(get_db),
):
    """
    Delete a service template.

    **Warning**: This will also delete all deployments using this service template
    due to CASCADE constraints.

    - **service_id**: Service UUID
    """
    success = delete_service(db, str(service_id))
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Service {service_id} not found",
        )
