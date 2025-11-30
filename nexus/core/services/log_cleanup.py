"""
Log cleanup service for Nexus Core.

Periodically removes old log entries to prevent database bloat.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy.orm import Session

from nexus.core.db import delete_old_logs
from nexus.core.db.database import SessionLocal
from nexus.shared.config import CoreConfig

logger = logging.getLogger(__name__)


class LogCleanupService:
    """
    Background service that periodically deletes old log entries.

    Runs on a configurable interval and removes logs older than the retention period.
    """

    def __init__(self, config: CoreConfig):
        """
        Initialize the log cleanup service.

        Args:
            config: Core configuration with retention settings
        """
        self.config = config
        self.task: Optional[asyncio.Task] = None
        self.running = False

    async def start(self):
        """Start the log cleanup service."""
        if self.config.log_retention_days == 0:
            logger.info("Log retention disabled (retention_days=0), logs will be kept forever")
            return

        logger.info(
            f"Starting log cleanup service: "
            f"retention={self.config.log_retention_days} days, "
            f"interval={self.config.log_cleanup_interval_hours} hours"
        )

        self.running = True
        self.task = asyncio.create_task(self._cleanup_loop())

    async def stop(self):
        """Stop the log cleanup service."""
        if self.task:
            self.running = False
            self.task.cancel()
            try:
                await self.task
            except asyncio.CancelledError:
                pass

        logger.info("Log cleanup service stopped")

    async def _cleanup_loop(self):
        """Background task that runs log cleanup periodically."""
        # Run cleanup on startup (after a short delay)
        await asyncio.sleep(60)  # Wait 1 minute after startup
        await self._run_cleanup()

        # Then run on interval
        interval_seconds = self.config.log_cleanup_interval_hours * 3600

        while self.running:
            try:
                await asyncio.sleep(interval_seconds)
                if self.running:
                    await self._run_cleanup()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in log cleanup loop: {e}", exc_info=True)
                # Continue running even if one cleanup fails

    async def _run_cleanup(self):
        """
        Run the log cleanup operation.

        Deletes logs older than the retention period.
        """
        try:
            # Calculate cutoff time
            cutoff = datetime.utcnow() - timedelta(days=self.config.log_retention_days)

            logger.info(f"Running log cleanup: deleting logs older than {cutoff.isoformat()}")

            # Use a database session
            db: Session = SessionLocal()
            try:
                deleted_count = delete_old_logs(db, before=cutoff)
                db.commit()

                if deleted_count > 0:
                    logger.info(f"Log cleanup complete: deleted {deleted_count} old log entries")
                else:
                    logger.debug("Log cleanup complete: no old logs to delete")

            finally:
                db.close()

        except Exception as e:
            logger.error(f"Failed to run log cleanup: {e}", exc_info=True)
