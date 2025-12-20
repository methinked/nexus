"""
Jobs API routes for Nexus Core.

Handles job submission, status tracking, and results.
"""

from typing import Any, Dict, Optional
from uuid import UUID

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from nexus.core.db import create_job, get_job, get_jobs, get_jobs_count, get_node, update_job_status
from nexus.core.db.database import get_db
from nexus.shared import BaseResponse, Job, JobCreate, JobList, JobStatus, JobType

router = APIRouter()


class JobUpdateRequest(BaseModel):
    """Request to update job status from agent."""

    status: str
    result: Optional[Dict[str, Any]] = None


@router.post("", response_model=Job, status_code=status.HTTP_201_CREATED)
async def submit_job(
    job: JobCreate,
    db: Session = Depends(get_db),
):
    """
    Submit a new job.

    Args:
        job: Job creation request

    Returns:
        Created job with ID and status

    Raises:
        404: Node not found
        503: Agent unavailable
    """
    # Validate that the node exists
    node = get_node(db, str(job.node_id))
    if not node:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Node {job.node_id} not found",
        )

    # Create job in database
    db_job = create_job(db, job)
    job_id = db_job.id

    # Send job to agent for execution
    try:
        agent_url = f"http://{node.ip_address}:8001/api/jobs/{job_id}/execute"

        # Prepare request payload
        payload = {
            "type": job.type.value,
            "payload": job.payload,
        }

        # Send to agent
        async with httpx.AsyncClient() as client:
            response = await client.post(
                agent_url,
                json=payload,
                timeout=10.0,
            )
            response.raise_for_status()

    except httpx.HTTPError as e:
        # Agent is unreachable or returned error
        # Mark job as failed
        update_job_status(
            db,
            job_id,
            JobStatus.FAILED,
            result={"error": f"Failed to send job to agent: {str(e)}"},
        )
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Agent unavailable: {str(e)}",
        )

    return Job.model_validate(db_job)


@router.get("", response_model=JobList)
def list_jobs(
    node_id: Optional[UUID] = Query(None),
    status_filter: Optional[JobStatus] = Query(None, alias="status"),
    job_type: Optional[JobType] = Query(None, alias="type"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
):
    """
    List all jobs.

    Query Parameters:
        node_id: Filter by node
        status: Filter by job status
        type: Filter by job type
        skip: Number of jobs to skip (pagination)
        limit: Maximum number of jobs to return

    Returns:
        List of jobs matching filters
    """
    # Get jobs from database
    db_jobs = get_jobs(
        db,
        skip=skip,
        limit=limit,
        node_id=str(node_id) if node_id else None,
        status=status_filter,
        job_type=job_type,
    )
    total = get_jobs_count(
        db,
        node_id=str(node_id) if node_id else None,
        status=status_filter,
        job_type=job_type,
    )

    # Convert to Pydantic models
    jobs = [Job.model_validate(job) for job in db_jobs]

    return JobList(jobs=jobs, total=total)


@router.get("/{job_id}", response_model=Job)
def get_job_details(
    job_id: UUID,
    db: Session = Depends(get_db),
):
    """
    Get job details and result.

    Args:
        job_id: UUID of the job

    Returns:
        Job with result if completed

    Raises:
        404: Job not found
    """
    # Get job from database
    db_job = get_job(db, str(job_id))
    if not db_job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job {job_id} not found",
        )

    return Job.model_validate(db_job)


@router.patch("/{job_id}", response_model=BaseResponse)
def update_job(
    job_id: UUID,
    update: JobUpdateRequest,
    db: Session = Depends(get_db),
):
    """
    Update job status and result (called by agent).

    Agents call this endpoint to report job execution results.

    Args:
        job_id: UUID of the job
        update: Job status and result

    Returns:
        Acknowledgment response

    Raises:
        404: Job not found
        400: Invalid status value
    """
    # Map string status to JobStatus enum
    status_map = {
        "pending": JobStatus.PENDING,
        "running": JobStatus.RUNNING,
        "completed": JobStatus.COMPLETED,
        "failed": JobStatus.FAILED,
    }

    job_status = status_map.get(update.status.lower())
    if not job_status:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid status: {update.status}. Must be one of: {list(status_map.keys())}",
        )

    # Update job in database
    db_job = update_job_status(
        db,
        str(job_id),
        job_status,
        result=update.result,
    )

    if not db_job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job {job_id} not found",
        )

    return BaseResponse(message="Job status updated")
