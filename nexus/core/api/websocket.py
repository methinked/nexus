"""
WebSocket API endpoints for real-time updates.
"""

import logging
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from nexus.core.services.websocket_manager import manager

logger = logging.getLogger(__name__)

router = APIRouter()


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint for real-time updates.

    Clients connect here to receive real-time events:
    - metric_update: New metrics from nodes
    - node_status: Node online/offline changes
    - job_update: Job status changes
    - log_entry: New log entries
    """
    client_id = f"{websocket.client.host}:{websocket.client.port}"
    await manager.connect(websocket, client_id)

    try:
        # Send initial connection success message
        await manager.send_personal(websocket, {
            "type": "connection",
            "data": {
                "status": "connected",
                "message": "WebSocket connection established",
                "client_id": client_id
            }
        })

        # Keep connection alive and handle incoming messages
        while True:
            # Wait for messages from client (e.g., ping/pong)
            data = await websocket.receive_text()

            # Handle ping/pong for keepalive
            if data == "ping":
                await manager.send_personal(websocket, {
                    "type": "pong",
                    "data": {}
                })

    except WebSocketDisconnect:
        await manager.disconnect(websocket)
        logger.info(f"Client {client_id} disconnected normally")
    except Exception as e:
        logger.error(f"WebSocket error for client {client_id}: {e}")
        await manager.disconnect(websocket)
