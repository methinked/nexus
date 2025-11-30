"""
Terminal API for Nexus Agent.

Provides WebSocket-based remote terminal access (Imperium module).
"""

import asyncio
import logging
import os
import pty
import select
import struct
import termios
from typing import Optional

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)
router = APIRouter()


class TerminalSession:
    """
    Manages a pseudo-terminal session.

    Spawns a shell in a PTY and handles bidirectional I/O over WebSocket.
    """

    def __init__(self, websocket: WebSocket):
        self.websocket = websocket
        self.master_fd: Optional[int] = None
        self.pid: Optional[int] = None
        self.shell = os.environ.get("SHELL", "/bin/bash")

    async def start(self):
        """Start the terminal session."""
        try:
            # Spawn a new PTY with shell
            self.pid, self.master_fd = pty.fork()

            if self.pid == 0:
                # Child process - exec the shell
                os.execvp(self.shell, [self.shell])
            else:
                # Parent process - handle I/O
                logger.info(f"Terminal session started: PID={self.pid}, Shell={self.shell}")
                await self._handle_io()

        except Exception as e:
            logger.error(f"Error starting terminal session: {e}")
            await self.websocket.send_json({"type": "error", "message": str(e)})
            raise
        finally:
            await self.cleanup()

    async def _handle_io(self):
        """Handle bidirectional I/O between WebSocket and PTY."""
        try:
            # Set PTY to non-blocking mode
            os.set_blocking(self.master_fd, False)

            while True:
                # Use select to check for data from PTY (with timeout)
                readable, _, _ = select.select([self.master_fd], [], [], 0.1)

                # Read from PTY if data available
                if readable:
                    try:
                        data = os.read(self.master_fd, 4096)
                        if data:
                            # Send PTY output to WebSocket
                            await self.websocket.send_bytes(data)
                        else:
                            # EOF - shell exited
                            logger.info("Shell process exited")
                            break
                    except OSError:
                        # PTY closed
                        break

                # Check for WebSocket messages (non-blocking)
                try:
                    message = await asyncio.wait_for(
                        self.websocket.receive(),
                        timeout=0.1
                    )

                    if message["type"] == "websocket.disconnect":
                        logger.info("WebSocket disconnected")
                        break
                    elif message["type"] == "websocket.receive":
                        # Handle different message types
                        if "bytes" in message:
                            # Input from user
                            os.write(self.master_fd, message["bytes"])
                        elif "text" in message:
                            # Handle control messages (resize, etc.)
                            await self._handle_control_message(message["text"])

                except asyncio.TimeoutError:
                    # No WebSocket message - continue
                    pass

        except WebSocketDisconnect:
            logger.info("WebSocket disconnected")
        except Exception as e:
            logger.error(f"Error in terminal I/O: {e}")
            raise

    async def _handle_control_message(self, message: str):
        """Handle control messages from client (resize, etc.)."""
        try:
            import json
            data = json.loads(message)

            if data.get("type") == "resize":
                # Resize PTY
                rows = data.get("rows", 24)
                cols = data.get("cols", 80)
                self._resize_pty(rows, cols)

        except Exception as e:
            logger.error(f"Error handling control message: {e}")

    def _resize_pty(self, rows: int, cols: int):
        """Resize the PTY window."""
        if self.master_fd is not None:
            try:
                winsize = struct.pack("HHHH", rows, cols, 0, 0)
                import fcntl
                fcntl.ioctl(self.master_fd, termios.TIOCSWINSZ, winsize)
                logger.debug(f"PTY resized to {rows}x{cols}")
            except Exception as e:
                logger.error(f"Error resizing PTY: {e}")

    async def cleanup(self):
        """Clean up terminal session."""
        if self.master_fd is not None:
            try:
                os.close(self.master_fd)
                logger.info("PTY master FD closed")
            except Exception as e:
                logger.error(f"Error closing PTY: {e}")

        if self.pid is not None:
            try:
                import signal
                os.kill(self.pid, signal.SIGTERM)
                os.waitpid(self.pid, 0)
                logger.info(f"Shell process {self.pid} terminated")
            except Exception as e:
                logger.error(f"Error killing shell process: {e}")


@router.websocket("/terminal")
async def terminal_websocket(websocket: WebSocket):
    """
    WebSocket endpoint for terminal access.

    Provides a pseudo-terminal session over WebSocket.
    Messages:
        - bytes: User input (stdin)
        - text: Control messages (resize, etc.)
    """
    await websocket.accept()
    logger.info(f"Terminal WebSocket connection accepted from {websocket.client}")

    session = TerminalSession(websocket)
    try:
        await session.start()
    except Exception as e:
        logger.error(f"Terminal session error: {e}")
        try:
            await websocket.send_json({"type": "error", "message": str(e)})
        except:
            pass
    finally:
        await session.cleanup()
        try:
            await websocket.close()
        except:
            pass


@router.get("/terminal/test")
async def terminal_test():
    """Test endpoint to verify terminal API is loaded."""
    return JSONResponse({
        "status": "ok",
        "message": "Terminal API ready",
        "shell": os.environ.get("SHELL", "/bin/bash")
    })
