"""
Job queue service for Nexus Agent.

Manages pending jobs and coordinates execution.
"""

import asyncio
import logging
from collections import deque
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Optional
from uuid import UUID

from nexus.shared import JobStatus, JobType

logger = logging.getLogger(__name__)


@dataclass
class QueuedJob:
    """
    Represents a job in the queue.
    """

    job_id: UUID
    job_type: JobType
    payload: Dict
    queued_at: datetime
    status: JobStatus = JobStatus.PENDING
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    result: Optional[Dict] = None
    error: Optional[str] = None


class JobQueue:
    """
    In-memory job queue for the agent.

    Stores pending jobs and tracks their execution status.
    """

    def __init__(self, max_concurrent: int = 2):
        """
        Initialize the job queue.

        Args:
            max_concurrent: Maximum number of jobs to run concurrently
        """
        self.queue: deque[QueuedJob] = deque()
        self.running: Dict[UUID, QueuedJob] = {}
        self.completed: Dict[UUID, QueuedJob] = {}
        self.max_concurrent = max_concurrent
        self._lock = asyncio.Lock()

    async def enqueue(self, job_id: UUID, job_type: JobType, payload: Dict) -> QueuedJob:
        """
        Add a job to the queue.

        Args:
            job_id: UUID of the job
            job_type: Type of job (OCR, SHELL, SYNC)
            payload: Job-specific payload data

        Returns:
            The queued job
        """
        async with self._lock:
            job = QueuedJob(
                job_id=job_id,
                job_type=job_type,
                payload=payload,
                queued_at=datetime.utcnow(),
            )
            self.queue.append(job)
            logger.info(f"Job {job_id} ({job_type.value}) added to queue")
            return job

    async def dequeue(self) -> Optional[QueuedJob]:
        """
        Get the next pending job if we have capacity.

        Returns:
            Next job to execute, or None if queue is empty or at capacity
        """
        async with self._lock:
            # Check if we're at capacity
            if len(self.running) >= self.max_concurrent:
                return None

            # Get next job from queue
            if not self.queue:
                return None

            job = self.queue.popleft()
            job.status = JobStatus.RUNNING
            job.started_at = datetime.utcnow()
            self.running[job.job_id] = job

            logger.info(f"Job {job.job_id} dequeued for execution")
            return job

    async def mark_completed(
        self, job_id: UUID, success: bool = True, result: Optional[Dict] = None, error: Optional[str] = None
    ):
        """
        Mark a job as completed.

        Args:
            job_id: UUID of the job
            success: Whether the job completed successfully
            result: Job result data
            error: Error message if job failed
        """
        async with self._lock:
            if job_id not in self.running:
                logger.warning(f"Attempted to complete unknown job {job_id}")
                return

            job = self.running.pop(job_id)
            job.status = JobStatus.COMPLETED if success else JobStatus.FAILED
            job.completed_at = datetime.utcnow()
            job.result = result
            job.error = error

            # Move to completed dict (keep recent 100)
            self.completed[job_id] = job
            if len(self.completed) > 100:
                # Remove oldest
                oldest = min(self.completed.keys(), key=lambda k: self.completed[k].completed_at)
                del self.completed[oldest]

            status_str = "successfully" if success else "with error"
            logger.info(f"Job {job_id} completed {status_str}")

    async def get_status(self, job_id: UUID) -> Optional[QueuedJob]:
        """
        Get the status of a job.

        Args:
            job_id: UUID of the job

        Returns:
            Job info if found, None otherwise
        """
        async with self._lock:
            # Check running jobs
            if job_id in self.running:
                return self.running[job_id]

            # Check completed jobs
            if job_id in self.completed:
                return self.completed[job_id]

            # Check queued jobs
            for job in self.queue:
                if job.job_id == job_id:
                    return job

            return None

    async def get_queue_size(self) -> int:
        """Get the number of pending jobs in queue."""
        async with self._lock:
            return len(self.queue)

    async def get_running_count(self) -> int:
        """Get the number of currently running jobs."""
        async with self._lock:
            return len(self.running)
