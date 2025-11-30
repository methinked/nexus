"""
Metrics collection service for Nexus Agent.

Collects system metrics and sends them to Core.
"""

import asyncio
import logging
from datetime import datetime
from uuid import UUID

from nexus.shared import AgentConfig, MetricCreate

logger = logging.getLogger(__name__)


class MetricsCollector:
    """
    Background service that collects and reports system metrics.
    """

    def __init__(self, config: AgentConfig, node_id: UUID, api_token: str):
        """
        Initialize metrics collector.

        Args:
            config: Agent configuration
            node_id: UUID of this node
            api_token: API token for authentication
        """
        self.config = config
        self.node_id = node_id
        self.api_token = api_token
        self._task: asyncio.Task | None = None
        self._running = False

    async def start(self):
        """Start the metrics collection background task."""
        if self._running:
            logger.warning("Metrics collector already running")
            return

        self._running = True
        self._task = asyncio.create_task(self._collect_loop())
        logger.info(
            f"Metrics collector started (interval: {self.config.metrics_interval}s)"
        )

    async def stop(self):
        """Stop the metrics collection background task."""
        if not self._running:
            return

        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass

        logger.info("Metrics collector stopped")

    async def _collect_loop(self):
        """Main collection loop."""
        while self._running:
            try:
                await self._collect_and_send()
            except Exception as e:
                logger.error(f"Error collecting metrics: {e}")

            await asyncio.sleep(self.config.metrics_interval)

    async def _collect_and_send(self):
        """Collect metrics and send to Core."""
        # TODO: Use psutil to collect actual metrics
        # TODO: Use vcgencmd for Pi temperature (if available)
        # TODO: Send metrics to Core via HTTP POST

        metrics = self._collect_metrics()
        await self._send_metrics(metrics)

    def _collect_metrics(self) -> MetricCreate:
        """
        Collect current system metrics.

        Returns:
            Metrics data

        TODO: Implement with psutil
        TODO: Add temperature reading for Raspberry Pi
        """
        # Placeholder - would use psutil in real implementation
        return MetricCreate(
            node_id=self.node_id,
            timestamp=datetime.utcnow(),
            cpu_percent=0.0,
            memory_percent=0.0,
            disk_percent=0.0,
            temperature=None,
        )

    async def _send_metrics(self, metrics: MetricCreate):
        """
        Send metrics to Core.

        Args:
            metrics: Metrics to send

        TODO: Implement HTTP POST to Core
        TODO: Handle authentication with api_token
        TODO: Handle network errors gracefully
        """
        # TODO: Use httpx to POST to {core_url}/api/metrics
        # TODO: Include Authorization header with bearer token
        # TODO: Retry on failure
        logger.debug(f"Would send metrics: {metrics}")
