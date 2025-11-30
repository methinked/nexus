"""
Job dispatcher service for Nexus Agent.

Coordinates job execution by pulling from queue and routing to executors.
"""

import asyncio
import logging
from typing import Optional

import httpx

from nexus.agent.modules.shell import ShellExecutor
from nexus.agent.services.job_queue import JobQueue, QueuedJob
from nexus.shared import AgentConfig, JobType

logger = logging.getLogger(__name__)


class JobDispatcher:
    """
    Background service that dispatches jobs from queue to executors.

    Polls the job queue, executes jobs using appropriate executors,
    and reports results back to Core.
    """

    def __init__(self, config: AgentConfig, job_queue: JobQueue, node_id: str, api_token: str):
        """
        Initialize the job dispatcher.

        Args:
            config: Agent configuration
            job_queue: Job queue instance
            node_id: UUID of this agent node
            api_token: JWT token for Core API authentication
        """
        self.config = config
        self.job_queue = job_queue
        self.node_id = node_id
        self.api_token = api_token
        self.running = False
        self.task: Optional[asyncio.Task] = None

        # Initialize executors
        self.shell_executor = ShellExecutor()
        # TODO: Initialize OCR and Sync executors when implemented

    async def start(self):
        """Start the job dispatcher service."""
        logger.info("Starting job dispatcher service...")
        self.running = True
        self.task = asyncio.create_task(self._dispatch_loop())
        logger.info("Job dispatcher service started")

    async def stop(self):
        """Stop the job dispatcher service."""
        logger.info("Stopping job dispatcher service...")
        self.running = False
        if self.task:
            self.task.cancel()
            try:
                await self.task
            except asyncio.CancelledError:
                pass
        logger.info("Job dispatcher service stopped")

    async def _dispatch_loop(self):
        """
        Main dispatcher loop.

        Continuously polls queue for jobs and dispatches them.
        """
        while self.running:
            try:
                # Check if there are jobs to process
                job = await self.job_queue.dequeue()

                if job:
                    # Execute job in background (don't wait)
                    asyncio.create_task(self._execute_job(job))
                else:
                    # No jobs available, wait before checking again
                    await asyncio.sleep(1)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in dispatcher loop: {e}", exc_info=True)
                await asyncio.sleep(5)  # Wait before retrying

    async def _execute_job(self, job: QueuedJob):
        """
        Execute a single job.

        Args:
            job: The job to execute
        """
        logger.info(f"Executing job {job.job_id} (type: {job.job_type.value})")

        try:
            # Route to appropriate executor
            if job.job_type == JobType.SHELL:
                result = await self.shell_executor.execute(job.payload)
            elif job.job_type == JobType.OCR:
                # TODO: Implement OCR executor
                result = {"success": False, "error": "OCR not yet implemented"}
            elif job.job_type == JobType.SYNC:
                # TODO: Implement Sync executor
                result = {"success": False, "error": "Sync not yet implemented"}
            else:
                result = {"success": False, "error": f"Unknown job type: {job.job_type}"}

            # Mark job as completed in queue
            await self.job_queue.mark_completed(
                job.job_id,
                success=result.success if hasattr(result, "success") else result.get("success", False),
                result=result.model_dump() if hasattr(result, "model_dump") else result,
                error=result.error if hasattr(result, "error") else result.get("error"),
            )

            # Report result back to Core
            await self._report_result(job.job_id, result)

        except Exception as e:
            logger.error(f"Error executing job {job.job_id}: {e}", exc_info=True)
            await self.job_queue.mark_completed(
                job.job_id,
                success=False,
                error=f"Execution error: {str(e)}",
            )

    async def _report_result(self, job_id, result):
        """
        Report job result back to Core.

        Args:
            job_id: UUID of the completed job
            result: Job result data
        """
        try:
            headers = {
                "Authorization": f"Bearer {self.api_token}",
                "Content-Type": "application/json",
            }

            payload = {
                "status": "completed" if (result.success if hasattr(result, "success") else result.get("success")) else "failed",
                "result": result.model_dump() if hasattr(result, "model_dump") else result,
            }

            async with httpx.AsyncClient() as client:
                response = await client.patch(
                    f"{self.config.core_url}/api/jobs/{job_id}",
                    json=payload,
                    headers=headers,
                    timeout=10.0,
                )
                response.raise_for_status()
                logger.info(f"Job {job_id} result reported to Core")

        except Exception as e:
            logger.error(f"Failed to report job result to Core: {e}")
            # Don't raise - job is still marked complete locally
