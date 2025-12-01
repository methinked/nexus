"""
WebSocket Connection Manager for Real-time Updates.

Manages WebSocket connections and broadcasts events to connected clients.
"""

import asyncio
import json
import logging
from typing import Dict, List, Set
from fastapi import WebSocket

logger = logging.getLogger(__name__)


class ConnectionManager:
    """Manages WebSocket connections and broadcasts events."""

    def __init__(self):
        """Initialize the connection manager."""
        self.active_connections: List[WebSocket] = []
        self.connection_ids: Dict[WebSocket, str] = {}
        self._lock = asyncio.Lock()

    async def connect(self, websocket: WebSocket, client_id: str = None):
        """
        Accept and register a new WebSocket connection.

        Args:
            websocket: WebSocket connection to register
            client_id: Optional client identifier
        """
        await websocket.accept()
        async with self._lock:
            self.active_connections.append(websocket)
            if client_id:
                self.connection_ids[websocket] = client_id

        logger.info(f"WebSocket connected: {client_id or 'anonymous'} (total: {len(self.active_connections)})")

    async def disconnect(self, websocket: WebSocket):
        """
        Remove a WebSocket connection.

        Args:
            websocket: WebSocket connection to remove
        """
        async with self._lock:
            if websocket in self.active_connections:
                self.active_connections.remove(websocket)
            client_id = self.connection_ids.pop(websocket, None)

        logger.info(f"WebSocket disconnected: {client_id or 'anonymous'} (total: {len(self.active_connections)})")

    async def broadcast(self, message: dict):
        """
        Broadcast a message to all connected clients.

        Args:
            message: Dictionary to send as JSON
        """
        if not self.active_connections:
            return

        message_json = json.dumps(message)
        disconnected = []

        for connection in self.active_connections:
            try:
                await connection.send_text(message_json)
            except Exception as e:
                logger.warning(f"Failed to send message to client: {e}")
                disconnected.append(connection)

        # Clean up disconnected clients
        if disconnected:
            async with self._lock:
                for connection in disconnected:
                    if connection in self.active_connections:
                        self.active_connections.remove(connection)
                    self.connection_ids.pop(connection, None)

    async def send_personal(self, websocket: WebSocket, message: dict):
        """
        Send a message to a specific client.

        Args:
            websocket: Target WebSocket connection
            message: Dictionary to send as JSON
        """
        try:
            await websocket.send_text(json.dumps(message))
        except Exception as e:
            logger.warning(f"Failed to send personal message: {e}")
            await self.disconnect(websocket)

    async def broadcast_event(self, event_type: str, data: dict):
        """
        Broadcast an event with type and data.

        Args:
            event_type: Type of event (e.g., 'metric_update', 'node_status', 'job_update')
            data: Event data
        """
        await self.broadcast({
            "type": event_type,
            "data": data
        })

    def get_connection_count(self) -> int:
        """Get the number of active connections."""
        return len(self.active_connections)


# Global connection manager instance
manager = ConnectionManager()
