"""
Metrics collection service for Nexus Agent.

Collects system metrics and sends them to Core.
"""

import asyncio
import logging
import platform
import shutil
import subprocess
from datetime import datetime
from pathlib import Path
from uuid import UUID

import httpx
import psutil

from nexus.agent.services.storage import get_all_disks
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
        metrics = self._collect_metrics()
        await self._send_metrics(metrics)

    def _collect_metrics(self) -> MetricCreate:
        """
        Collect current system metrics using psutil.

        Returns:
            Metrics data
        """
        # Collect CPU usage (non-blocking, returns usage since last call)
        # First call will return 0.0, subsequent calls return avg since last call
        cpu_percent = psutil.cpu_percent(interval=0)

        # Collect memory usage
        memory = psutil.virtual_memory()
        memory_percent = memory.percent

        # Collect all disk information (Phase 6.5 - Multi-disk support)
        try:
            disks = get_all_disks()

            # Log disk information for debugging
            if disks:
                logger.debug(f"Detected {len(disks)} disk(s):")
                for disk in disks:
                    logger.debug(
                        f"  {disk.mount_point}: {disk.type.value}, "
                        f"{disk.usage_percent:.1f}% used, "
                        f"Docker={disk.is_docker_data}, Nexus={disk.is_nexus_data}"
                    )

            # For backward compatibility, use root filesystem for disk_percent
            root_disk = next((d for d in disks if d.is_system), None)
            disk_percent = root_disk.usage_percent if root_disk else 0.0

        except Exception as e:
            logger.warning(f"Failed to collect disk info, using fallback: {e}")
            # Fallback to old method
            disk = psutil.disk_usage('/')
            disk_percent = disk.percent

        # Try to get temperature (Raspberry Pi specific)
        temperature = self._get_temperature()

        # TODO Phase 6.5.2: Add disks to MetricCreate once database schema updated
        return MetricCreate(
            node_id=self.node_id,
            timestamp=datetime.utcnow(),
            cpu_percent=cpu_percent,
            memory_percent=memory_percent,
            disk_percent=disk_percent,
            temperature=temperature,
        )

    def _get_temperature(self) -> float | None:
        """
        Get CPU temperature.

        For Raspberry Pi, uses vcgencmd. For other systems, tries psutil sensors.
        Falls back to None if temperature cannot be read.

        Returns:
            Temperature in Celsius, or None if unavailable
        """
        # Try vcgencmd for Raspberry Pi
        if shutil.which('vcgencmd'):
            try:
                result = subprocess.run(
                    ['vcgencmd', 'measure_temp'],
                    capture_output=True,
                    text=True,
                    timeout=2,
                )
                if result.returncode == 0:
                    # Output format: "temp=42.8'C"
                    temp_str = result.stdout.strip()
                    if 'temp=' in temp_str:
                        temp = float(temp_str.split('=')[1].split("'")[0])
                        return temp
            except Exception as e:
                logger.debug(f"Failed to read vcgencmd temperature: {e}")

        # Try psutil sensors (Linux)
        if hasattr(psutil, 'sensors_temperatures'):
            try:
                temps = psutil.sensors_temperatures()
                # Try common sensor names
                for sensor_name in ['coretemp', 'cpu_thermal', 'k10temp']:
                    if sensor_name in temps:
                        sensor_data = temps[sensor_name]
                        if sensor_data:
                            return sensor_data[0].current
            except Exception as e:
                logger.debug(f"Failed to read psutil temperature: {e}")

        return None

    async def _send_metrics(self, metrics: MetricCreate):
        """
        Send metrics to Core via HTTP POST.

        Args:
            metrics: Metrics to send
        """
        url = f"{self.config.core_url}/api/metrics"
        headers = {
            "Authorization": f"Bearer {self.api_token}",
            "Content-Type": "application/json",
        }

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    url,
                    json=metrics.model_dump(mode='json'),
                    headers=headers,
                    timeout=10.0,
                )
                response.raise_for_status()
                logger.debug(f"Metrics sent successfully: CPU={metrics.cpu_percent:.1f}% "
                           f"MEM={metrics.memory_percent:.1f}% "
                           f"DISK={metrics.disk_percent:.1f}%")

        except httpx.HTTPStatusError as e:
            logger.error(f"Failed to send metrics: HTTP {e.response.status_code}")
        except httpx.ConnectError:
            logger.error(f"Failed to connect to Core at {self.config.core_url}")
        except Exception as e:
            logger.error(f"Unexpected error sending metrics: {e}")
