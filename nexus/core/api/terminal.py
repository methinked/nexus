"""
Terminal proxy API for Nexus Core.

Provides WebSocket proxy between CLI clients and Agent terminals.
"""

import asyncio
import logging
from typing import Optional
from uuid import UUID

import httpx
from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect, status
from sqlalchemy.orm import Session

from nexus.core.db import get_node
from nexus.core.db.database import get_db

logger = logging.getLogger(__name__)
router = APIRouter()


class TerminalProxy:
    """
    WebSocket proxy between CLI client and Agent terminal.

    Relays messages bidirectionally:
    - CLI -> Core -> Agent (input)
    - Agent -> Core -> CLI (output)
    """

    def __init__(self, cli_ws: WebSocket, agent_url: str):
        self.cli_ws = cli_ws
        self.agent_url = agent_url
        self.agent_ws: Optional[httpx.WebSocketUpgrade] = None
        self.running = False

    async def start(self):
        """Start the proxy relay."""
        try:
            # Connect to Agent's WebSocket terminal
            async with httpx.AsyncClient() as client:
                async with client.ws_connect(self.agent_url) as agent_ws:
                    self.agent_ws = agent_ws
                    self.running = True
                    logger.info(f"Proxy connected to agent: {self.agent_url}")

                    # Run bidirectional relay
                    await self._relay()

        except httpx.ConnectError as e:
            logger.error(f"Failed to connect to agent: {e}")
            await self.cli_ws.send_json({
                "type": "error",
                "message": f"Could not connect to agent: {e}"
            })
        except Exception as e:
            logger.error(f"Proxy error: {e}")
            await self.cli_ws.send_json({
                "type": "error",
                "message": f"Proxy error: {e}"
            })
        finally:
            self.running = False

    async def _relay(self):
        """Relay messages bidirectionally between CLI and Agent."""
        try:
            # Create tasks for both directions
            cli_to_agent = asyncio.create_task(self._relay_cli_to_agent())
            agent_to_cli = asyncio.create_task(self._relay_agent_to_cli())

            # Wait for either task to complete (indicating a disconnect)
            done, pending = await asyncio.wait(
                [cli_to_agent, agent_to_cli],
                return_when=asyncio.FIRST_COMPLETED
            )

            # Cancel remaining tasks
            for task in pending:
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass

        except Exception as e:
            logger.error(f"Relay error: {e}")

    async def _relay_cli_to_agent(self):
        """Relay messages from CLI to Agent."""
        try:
            while self.running:
                message = await self.cli_ws.receive()

                if message["type"] == "websocket.disconnect":
                    logger.info("CLI disconnected")
                    break

                # Forward to agent
                if "bytes" in message:
                    await self.agent_ws.send_bytes(message["bytes"])
                elif "text" in message:
                    await self.agent_ws.send_text(message["text"])

        except WebSocketDisconnect:
            logger.info("CLI WebSocket disconnected")
        except Exception as e:
            logger.error(f"Error relaying CLI to Agent: {e}")

    async def _relay_agent_to_cli(self):
        """Relay messages from Agent to CLI."""
        try:
            while self.running:
                try:
                    # Receive from agent
                    message = await asyncio.wait_for(
                        self.agent_ws.receive_bytes(),
                        timeout=30.0  # 30 second timeout
                    )

                    # Forward to CLI
                    await self.cli_ws.send_bytes(message)

                except asyncio.TimeoutError:
                    # Send keepalive ping
                    try:
                        await self.cli_ws.send_json({"type": "ping"})
                    except:
                        break

        except Exception as e:
            logger.error(f"Error relaying Agent to CLI: {e}")


@router.websocket("/terminal/{node_id}")
async def terminal_proxy(
    websocket: WebSocket,
    node_id: UUID,
    db: Session = Depends(get_db),
):
    """
    WebSocket proxy endpoint for terminal access.

    Connects CLI client to Agent's terminal WebSocket.

    Path Parameters:
        node_id: UUID of the node to connect to

    Protocol:
        - Client sends bytes: user input (forwarded to agent)
        - Client sends text: control messages like resize (forwarded to agent)
        - Client receives bytes: terminal output (from agent)
    """
    await websocket.accept()
    logger.info(f"Terminal proxy connection from {websocket.client} to node {node_id}")

    # Validate node exists
    node = get_node(db, str(node_id))
    if not node:
        await websocket.send_json({
            "type": "error",
            "message": f"Node {node_id} not found"
        })
        await websocket.close()
        return

    # Check node is online
    if node.status != "online":
        await websocket.send_json({
            "type": "error",
            "message": f"Node {node_id} is {node.status}, not online"
        })
        await websocket.close()
        return

    # Build Agent WebSocket URL
    # Note: Using ws:// for now, should be wss:// in production
    agent_ws_url = f"ws://{node.ip_address}:8001/api/terminal"
    logger.info(f"Connecting to agent terminal: {agent_ws_url}")

    # Create and start proxy
    proxy = TerminalProxy(websocket, agent_ws_url)
    try:
        await proxy.start()
    except Exception as e:
        logger.error(f"Proxy error: {e}")
    finally:
        try:
            await websocket.close()
        except:
            pass


@router.get("/terminal/{node_id}/test")
async def terminal_test(node_id: UUID, db: Session = Depends(get_db)):
    """Test endpoint to verify terminal proxy is configured correctly."""
    node = get_node(db, str(node_id))
    if not node:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Node {node_id} not found"
        )

    agent_url = f"http://{node.ip_address}:8001/api/terminal/test"

    return {
        "status": "ok",
        "node_id": str(node_id),
        "node_name": node.name,
        "node_status": node.status,
        "agent_ip": node.ip_address,
        "agent_terminal_url": agent_url,
        "ws_url": f"ws://{node.ip_address}:8001/api/terminal"
    }
