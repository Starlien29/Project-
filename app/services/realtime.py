"""Real-time alert delivery via SSE (FR-10)."""
import asyncio
import json
from typing import AsyncGenerator

from app.models.alert import Alert


class SSEManager:
    """In-process SSE connection manager; broadcasts alerts to all subscribers."""

    def __init__(self):
        self._subscriptions: list[asyncio.Queue] = []

    def subscribe(self) -> asyncio.Queue:
        q: asyncio.Queue = asyncio.Queue()
        self._subscriptions.append(q)
        return q

    def unsubscribe(self, q: asyncio.Queue) -> None:
        if q in self._subscriptions:
            self._subscriptions.remove(q)

    async def broadcast_alert(self, alert_dict: dict) -> None:
        """Push alert to all connected clients (target <5s, FR-10)."""
        msg = f"data: {json.dumps(alert_dict)}\n\n"
        for q in list(self._subscriptions):
            try:
                q.put_nowait(msg)
            except asyncio.QueueFull:
                pass

    def broadcast_alert_sync(self, alert_dict: dict) -> None:
        """Sync version for use from sync route; schedules async broadcast."""
        try:
            loop = asyncio.get_running_loop()
            loop.create_task(self.broadcast_alert(alert_dict))
        except RuntimeError:
            asyncio.run(self.broadcast_alert(alert_dict))


sse_manager = SSEManager()


async def event_generator(queue: asyncio.Queue) -> AsyncGenerator[str, None]:
    """Yield SSE events from queue until disconnected."""
    while True:
        try:
            event = await asyncio.wait_for(queue.get(), timeout=30.0)
            yield event
        except asyncio.TimeoutError:
            yield 'data: {"type":"ping"}\n\n'
