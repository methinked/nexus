"""
Inventory collection service for Nexus Agent.

Periodically collects system inventory (disks, containers) and pushes to Core.
This replaces the old "Pull" model where Core would query Agent on demand.
"""

import asyncio
import logging
from typing import Any, Dict, List
from uuid import UUID

import httpx

from nexus.agent.services.storage import get_all_disks
from nexus.shared import AgentConfig, DiskInfo, InventoryUpdate

logger = logging.getLogger(__name__)


class InventoryCollector:
    """
    Background service that collects and pushes system inventory.
    """

    def __init__(self, config: AgentConfig, node_id: UUID, api_token: str):
        """
        Initialize inventory collector.

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
        self._interval = 300.0  # Push every 5 minutes (reduced from 60s)

    async def start(self):
        """Start the inventory collection background task."""
        if self._running:
            logger.warning("Inventory collector already running")
            return

        self._running = True
        self._task = asyncio.create_task(self._collect_loop())
        logger.info(f"Inventory collector started (interval: {self._interval}s)")
        
        # Trigger immediate collection
        asyncio.create_task(self._collect_and_send())

    async def stop(self):
        """Stop the inventory collection background task."""
        if not self._running:
            return

        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass

        logger.info("Inventory collector stopped")

    async def _collect_loop(self):
        """Main collection loop."""
        while self._running:
            try:
                await asyncio.sleep(self._interval)
                await self._collect_and_send()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in inventory loop: {e}")
                await asyncio.sleep(10)  # Backoff on error

    async def _collect_and_send(self):
        """Collect inventory and send to Core."""
        try:
            inventory = await self._collect_inventory()
            await self._send_inventory(inventory)
        except Exception as e:
            logger.error(f"Failed to collect/send inventory: {e}")

    async def _collect_inventory(self) -> InventoryUpdate:
        """
        Collect current inventory.

        Returns:
            InventoryUpdate model
        """
        # 1. Collect Disks
        try:
            disks = get_all_disks()
        except Exception as e:
            logger.warning(f"Failed to collect disk info: {e}")
            disks = []

        # 2. Collect Containers
        containers = self._collect_containers()

        return InventoryUpdate(
            node_id=self.node_id,
            disks=disks,
            containers=containers
        )

    def _collect_containers(self) -> List[Dict[str, Any]]:
        """Collect running containers using Docker SDK."""
        try:
            import docker
            client = docker.from_env()
            containers = client.containers.list(all=True)
            
            container_list = []
            for c in containers:
                try:
                    # Basic extraction, matching the structure used in `nexus.agent.api.docker`
                    # We send a simplified dict that fits into our metadata schema
                    info = {
                        "id": c.id,
                        "short_id": c.short_id,
                        "name": c.name,
                        "status": c.status,
                        "image": c.image.tags[0] if c.image.tags else c.image.id,
                        "created": c.attrs.get("Created"),
                        "state": c.attrs.get("State", {}),
                        # Managed flag if labeled
                        "managed": c.labels.get("com.nexus.managed") == "true"
                    }
                    container_list.append(info)
                except Exception as c_err:
                    logger.warning(f"Error parsing container {c.short_id}: {c_err}")
                    
            return container_list
            
        except ImportError:
            logger.warning("Docker SDK not installed")
            return []
        except Exception as e:
            logger.warning(f"Failed to list containers: {e}")
            return []

    async def _send_inventory(self, inventory: InventoryUpdate):
        """
        Send inventory to Core via HTTP POST.
        """
        url = f"{self.config.core_url.rstrip('/')}/api/nodes/inventory"
        headers = {
            "Authorization": f"Bearer {self.api_token}",
            "Content-Type": "application/json",
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(
                url,
                json=inventory.model_dump(mode='json'),
                headers=headers,
                timeout=20.0,
            )
            response.raise_for_status()
            logger.debug(f"Inventory sent successfully ({len(inventory.disks)} disks, {len(inventory.containers)} containers)")
