"""
Log collection service for Nexus Agent.

Captures Python logs and forwards them to Core for centralized logging.
"""

import asyncio
import logging
from datetime import datetime
from queue import Queue
from typing import Optional
from uuid import UUID

import httpx

from nexus.shared import AgentConfig, LogCreate, LogLevel


class CoreLogHandler(logging.Handler):
    """
    Custom logging handler that forwards logs to Nexus Core.

    Buffers log records in a queue and sends them asynchronously to Core.
    """

    def __init__(
        self,
        node_id: UUID,
        api_token: str,
        core_url: str,
        queue_size: int = 1000,
    ):
        """
        Initialize the Core log handler.

        Args:
            node_id: UUID of this agent node
            api_token: JWT token for authentication
            core_url: URL of the Core server
            queue_size: Maximum size of the log queue
        """
        super().__init__()
        self.node_id = node_id
        self.api_token = api_token
        self.core_url = core_url
        self.log_queue: Queue = Queue(maxsize=queue_size)
        self.running = False

    def emit(self, record: logging.LogRecord):
        """
        Emit a log record to the queue.

        Args:
            record: LogRecord to send to Core
        """
        try:
            # Convert Python log level to Nexus LogLevel
            level_map = {
                logging.DEBUG: LogLevel.DEBUG,
                logging.INFO: LogLevel.INFO,
                logging.WARNING: LogLevel.WARNING,
                logging.ERROR: LogLevel.ERROR,
                logging.CRITICAL: LogLevel.CRITICAL,
            }
            log_level = level_map.get(record.levelno, LogLevel.INFO)

            # Create log entry
            log_data = LogCreate(
                node_id=self.node_id,
                timestamp=datetime.fromtimestamp(record.created),
                level=log_level,
                source=record.name,  # Module name (e.g., "nexus.agent.main")
                message=self.format(record),
                extra={
                    "funcName": record.funcName,
                    "lineno": record.lineno,
                    "pathname": record.pathname,
                },
            )

            # Add to queue (non-blocking)
            if not self.log_queue.full():
                self.log_queue.put(log_data)

        except Exception:
            # Don't raise exceptions in logging handler
            # This prevents logging failures from crashing the app
            self.handleError(record)


class LogCollector:
    """
    Service that sends queued logs to Core.

    Runs in background, periodically sending batched logs to Core.
    """

    def __init__(
        self,
        config: AgentConfig,
        node_id: UUID,
        api_token: str,
    ):
        """
        Initialize the log collector.

        Args:
            config: Agent configuration
            node_id: UUID of this agent node
            api_token: JWT token for authentication
        """
        self.config = config
        self.node_id = node_id
        self.api_token = api_token
        self.handler: Optional[CoreLogHandler] = None
        self.task: Optional[asyncio.Task] = None
        self.logger = logging.getLogger(__name__)

    async def start(self):
        """Start the log collector service."""
        # Create and register the handler
        self.handler = CoreLogHandler(
            node_id=self.node_id,
            api_token=self.api_token,
            core_url=self.config.core_url,
        )

        # Set format
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        self.handler.setFormatter(formatter)

        # Set level (only send INFO and above to Core to reduce noise)
        self.handler.setLevel(logging.INFO)

        # Add to root logger
        logging.getLogger().addHandler(self.handler)

        self.logger.info("Log collection service started")

        # Start background task to send logs
        self.task = asyncio.create_task(self._send_logs_loop())

    async def stop(self):
        """Stop the log collector service."""
        if self.task:
            self.task.cancel()
            try:
                await self.task
            except asyncio.CancelledError:
                pass

        if self.handler:
            logging.getLogger().removeHandler(self.handler)

        self.logger.info("Log collection service stopped")

    async def _send_logs_loop(self):
        """Background task that sends logs to Core."""
        while True:
            try:
                await asyncio.sleep(30)  # Send logs every 30 seconds

                # Collect logs from queue
                logs_to_send = []
                while not self.handler.log_queue.empty() and len(logs_to_send) < 100:
                    log_data = self.handler.log_queue.get()
                    logs_to_send.append(log_data)

                if not logs_to_send:
                    continue

                # Send to Core
                await self._send_logs_batch(logs_to_send)

            except asyncio.CancelledError:
                raise
            except Exception as e:
                self.logger.error(f"Error sending logs to Core: {e}")

    async def _send_logs_batch(self, logs: list[LogCreate]):
        """
        Send a batch of logs to Core.

        Args:
            logs: List of log entries to send
        """
        headers = {
            "Authorization": f"Bearer {self.api_token}",
            "Content-Type": "application/json",
        }

        async with httpx.AsyncClient() as client:
            for log in logs:
                try:
                    response = await client.post(
                        f"{self.config.core_url}/api/logs",
                        json=log.model_dump(mode="json"),
                        headers=headers,
                        timeout=5.0,
                    )
                    response.raise_for_status()
                except Exception as e:
                    # Log error locally but don't re-raise
                    # (avoid infinite loop of logging failures)
                    self.logger.debug(f"Failed to send log to Core: {e}")
