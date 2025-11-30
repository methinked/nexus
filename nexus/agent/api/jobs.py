"""
Jobs API routes for Nexus Agent.

Handles job execution requests from Core.
"""

from datetime import datetime
from typing import Any, Dict
from uuid import UUID

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from nexus.shared import JobStatus, JobType

router = APIRouter()


class JobExecutionRequest(BaseModel):
    """Request to execute a job."""

    type: JobType
    payload: Dict[str, Any]


class JobExecutionResponse(BaseModel):
    """Response for job execution start."""

    job_id: UUID
    status: JobStatus
    started_at: datetime


class JobStatusResponse(BaseModel):
    """Response for job status query."""

    job_id: UUID
    status: JobStatus
    result: Dict[str, Any] | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None


@router.post("/{job_id}/execute", response_model=JobExecutionResponse)
async def execute_job(job_id: UUID, request: JobExecutionRequest):
    """
    Execute a job (called by Core).

    Core sends a job execution request to the agent. The agent
    starts the job asynchronously and returns immediately.

    Args:
        job_id: UUID of the job
        request: Job type and payload

    Returns:
        Job execution acknowledgment

    TODO: Implement job dispatcher based on job type
    TODO: Queue job for background execution
    TODO: Return job status
    """
    # TODO: Validate job type
    # TODO: Queue job for execution based on type
    # TODO: Start background worker

    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Job execution not yet implemented",
    )


@router.get("/{job_id}/status", response_model=JobStatusResponse)
async def get_job_status(job_id: UUID):
    """
    Get job execution status.

    Core polls this endpoint to check job progress.

    Args:
        job_id: UUID of the job

    Returns:
        Current job status and result if completed

    TODO: Implement job status tracking
    TODO: Return job result when completed
    """
    # TODO: Query local job status
    # TODO: Return status and result

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Job {job_id} not found",
    )
