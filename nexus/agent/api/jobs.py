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
    queues the job for background execution and returns immediately.

    Args:
        job_id: UUID of the job
        request: Job type and payload

    Returns:
        Job execution acknowledgment
    """
    from nexus.agent.main import job_queue

    if not job_queue:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Job system not initialized",
        )

    # Enqueue the job
    queued_job = await job_queue.enqueue(job_id, request.type, request.payload)

    return JobExecutionResponse(
        job_id=job_id,
        status=JobStatus.PENDING,
        started_at=queued_job.queued_at,
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
    """
    from nexus.agent.main import job_queue

    if not job_queue:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Job system not initialized",
        )

    # Query job status from queue
    job = await job_queue.get_status(job_id)

    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job {job_id} not found",
        )

    return JobStatusResponse(
        job_id=job.job_id,
        status=job.status,
        result=job.result,
        started_at=job.started_at,
        completed_at=job.completed_at,
    )
