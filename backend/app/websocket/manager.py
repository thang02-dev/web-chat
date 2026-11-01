from typing import Dict, Set, Any
from fastapi import WebSocket
import json
import logging

logger = logging.getLogger("websocket")

class ConnectionManager:
    def __init__(self):
        # Maps user_id -> set of active WebSockets
        self.active_connections: Dict[str, Set[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, user_id: str):
        await websocket.accept()
        if user_id not in self.active_connections:
            self.active_connections[user_id] = set()
        self.active_connections[user_id].add(websocket)
        logger.info(f"User {user_id} connected. Active connections for user: {len(self.active_connections[user_id])}")

    def disconnect(self, websocket: WebSocket, user_id: str) -> bool:
        """Removes a socket. Returns True if the user now has 0 connections (fully offline)."""
        is_now_offline = False
        if user_id in self.active_connections:
            self.active_connections[user_id].discard(websocket)
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]
                is_now_offline = True
        logger.info(f"User {user_id} disconnected. Fully offline: {is_now_offline}")
        return is_now_offline

    def is_user_online(self, user_id: str) -> bool:
        return user_id in self.active_connections and len(self.active_connections[user_id]) > 0

    async def send_personal_message(self, message: dict[str, Any], user_id: str):
        """Sends a JSON message to all active sessions of a single user."""
        if user_id in self.active_connections:
            dead_sockets = set()
            payload_str = json.dumps(message, default=str)
            for socket in self.active_connections[user_id]:
                try:
                    await socket.send_text(payload_str)
                except Exception as e:
                    logger.warning(f"Error sending message to user {user_id}: {e}")
                    dead_sockets.add(socket)
            
            # Clean up dead sockets
            for dead in dead_sockets:
                self.active_connections[user_id].discard(dead)
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]

    async def broadcast_to_users(self, message: dict[str, Any], user_ids: list[str]):
        """Broadcasts a message to multiple specified users."""
        for uid in user_ids:
            await self.send_personal_message(message, uid)

    async def broadcast_all(self, message: dict[str, Any]):
        """Broadcasts a message to all active users on the server."""
        for uid in list(self.active_connections.keys()):
            await self.send_personal_message(message, uid)

manager = ConnectionManager()

