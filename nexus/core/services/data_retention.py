"""
Data retention service for Nexus Core.

Periodically removes old metric entries to prevent database bloat.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy.orm import Session

from nexus.core.db import delete_old_metrics
from nexus.core.db.database import SessionLocal
from nexus.shared.config import CoreConfig

logger = logging.getLogger(__name__)


class DataRetentionService:
    """
    Background service that periodically deletes old metric entries.

    Runs on a configurable interval and removes metrics older than the retention period.
    """

    def __init__(self, config: CoreConfig):
        """
        Initialize the data retention service.

        Args:
            config: Core configuration with retention settings
        """
        self.config = config
        self.task: Optional[asyncio.Task] = None
        self.running = False
        # Hardcoded retention period for metrics for now, or add to CoreConfig later
        # User requested 7 days.
        self.metrics_retention_days = 7
        self.cleanup_interval_hours = 24

    async def start(self):
        """Start the data retention service."""
        if self.metrics_retention_days == 0:
            logger.info("Metrics retention disabled (retention_days=0)")
            return

        logger.info(
            f"Starting data retention service: "
            f"retention={self.metrics_retention_days} days, "
            f"interval={self.cleanup_interval_hours} hours"
        )

        self.running = True
        self.task = asyncio.create_task(self._cleanup_loop())

    async def stop(self):
        """Stop the data retention service."""
        if self.task:
            self.running = False
            self.task.cancel()
            try:
                await self.task
            except asyncio.CancelledError:
                pass

        logger.info("Data retention service stopped")

    async def _cleanup_loop(self):
        """Background task that runs metrics cleanup periodically."""
        # Run cleanup on startup (after a slightly longer delay than logs)
        await asyncio.sleep(120)  # Wait 2 minutes after startup
        await self._run_cleanup()

        # Then run on interval
        interval_seconds = self.cleanup_interval_hours * 3600

        while self.running:
            try:
                await asyncio.sleep(interval_seconds)
                if self.running:
                    await self._run_cleanup()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in data retention loop: {e}", exc_info=True)

    async def _run_cleanup(self):
        """
        Run the metrics cleanup operation.

        Deletes metrics older than the retention period.
        """
        try:
            # Calculate cutoff time
            cutoff = datetime.utcnow() - timedelta(days=self.metrics_retention_days)

            logger.info(f"Running metrics cleanup: deleting metrics older than {cutoff.isoformat()}")

            # Use a database session
            db: Session = SessionLocal()
            try:
                deleted_count = delete_old_metrics(db, before=cutoff)
                
                if deleted_count > 0:
                    logger.info(f"Metrics cleanup complete: deleted {deleted_count} old metric entries")
                else:
                    logger.debug("Metrics cleanup complete: no old metrics to delete")

            finally:
                db.close()

        except Exception as e:
            logger.error(f"Failed to run metrics cleanup: {e}", exc_info=True)
