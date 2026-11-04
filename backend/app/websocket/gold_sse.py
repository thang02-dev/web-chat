import asyncio
import json
import logging
from typing import Set

logger = logging.getLogger("webchat.gold.sse")


class SSEManager:
    """Manages active Server-Sent Events (SSE) subscribers and broadcasts price updates."""

    def __init__(self):
        self._subscribers: Set[asyncio.Queue] = set()

    def subscribe(self) -> asyncio.Queue:
        """Register a new SSE client queue."""
        queue = asyncio.Queue()
        self._subscribers.add(queue)
        logger.info(f"New Gold SSE client connected. Active connections: {len(self._subscribers)}")
        return queue

    def unsubscribe(self, queue: asyncio.Queue):
        """Remove disconnected client queue."""
        self._subscribers.discard(queue)
        logger.info(f"Gold SSE client disconnected. Active connections: {len(self._subscribers)}")

    async def broadcast_price_update(self, saved_count: int):
        """Broadcast a price-update event to all active clients."""
        if not self._subscribers:
            logger.debug("No active SSE clients to broadcast to.")
            return

        logger.info(f"Broadcasting gold price-update to {len(self._subscribers)} client(s). Saved: {saved_count}")
        payload = {
            "saved": saved_count,
            "timestamp": int(asyncio.get_event_loop().time() * 1000)
        }
        event_message = f"event: price-update\ndata: {json.dumps(payload)}\n\n"

        for queue in list(self._subscribers):
            try:
                queue.put_nowait(event_message)
            except Exception as e:
                logger.debug(f"Failed to queue SSE event for subscriber: {e}")
                self._subscribers.discard(queue)

    @property
    def active_count(self) -> int:
        return len(self._subscribers)


gold_sse_manager = SSEManager()
