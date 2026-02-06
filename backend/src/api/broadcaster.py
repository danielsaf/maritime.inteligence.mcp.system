import asyncio
import json
import logging
from typing import List, Dict, Any
from fastapi import WebSocket

# Logger configuration
logger = logging.getLogger("Broadcaster")


class ConnectionManager:
    """
    Manages WebSocket connections and real-time message broadcasting.

    This class handles client registration, disconnection, and ensures
    that AIS updates and security alerts are pushed to all active frontends.
    """

    def __init__(self):
        """Initializes the manager with an empty list of active connections."""
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        """
        Accepts a new WebSocket connection and adds it to the active pool.

        Args:
            websocket (WebSocket): The incoming FastAPI WebSocket connection.
        """
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"🌐 New client connected. Active connections: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        """
        Removes a disconnected client from the active pool.

        Args:
            websocket (WebSocket): The WebSocket connection to remove.
        """
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            logger.info(f"🔌 Client disconnected. Remaining connections: {len(self.active_connections)}")

    async def broadcast(self, message: Dict[str, Any]):
        """
        Sends a JSON message to all currently connected clients.

        Uses asynchronous gathering to ensure high performance even with
        multiple connected clients.

        Args:
            message (Dict[str, Any]): The message payload to broadcast.
        """
        if not self.active_connections:
            return

        data = json.dumps(message)

        # Create tasks for parallel execution
        tasks = []
        for connection in self.active_connections:
            tasks.append(self._send_safe(connection, data))

        if tasks:
            await asyncio.gather(*tasks)

    async def _send_safe(self, websocket: WebSocket, message: str):
        """
        Safely sends a message to a single client and handles failures.

        If a send operation fails, the client is automatically disconnected
        to prevent system degradation.

        Args:
            websocket (WebSocket): Target connection.
            message (str): Serialized JSON string.
        """
        try:
            await websocket.send_text(message)
        except Exception as e:
            logger.error(f"❌ Failed to send message to client: {e}")
            self.disconnect(websocket)


# Global manager instance to be imported by main.py
manager = ConnectionManager()