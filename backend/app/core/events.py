"""Server-Sent Events (SSE) manager for real-time updates.

Manages per-party event queues so that all connected clients in a party
receive instant updates when balances, transactions, or payments change.
"""

import asyncio
import json
from collections import defaultdict
from typing import AsyncGenerator


class EventManager:
    """Manages SSE connections grouped by party."""

    def __init__(self):
        # party_id -> set of asyncio.Queue instances (one per connected client)
        self._party_queues: dict[int, set[asyncio.Queue]] = defaultdict(set)

    def subscribe(self, party_id: int) -> asyncio.Queue:
        """Add a new subscriber for a party. Returns a queue to read events from."""
        queue: asyncio.Queue = asyncio.Queue()
        self._party_queues[party_id].add(queue)
        count = len(self._party_queues[party_id])
        print(f"[SSE] +subscribe party={party_id} total={count}", flush=True)
        return queue

    def unsubscribe(self, party_id: int, queue: asyncio.Queue) -> None:
        """Remove a subscriber from a party."""
        self._party_queues[party_id].discard(queue)
        if not self._party_queues[party_id]:
            del self._party_queues[party_id]
            print(f"[SSE] -unsubscribe party={party_id} (last one)", flush=True)
        else:
            remaining = len(self._party_queues[party_id])
            print(f"[SSE] -unsubscribe party={party_id} remaining={remaining}", flush=True)

    async def broadcast(self, party_id: int, event_type: str, data: dict) -> None:
        """Send an event to all subscribers in a party."""
        queues = self._party_queues.get(party_id, set())
        print(f"[SSE] broadcast '{event_type}' party={party_id} subscribers={len(queues)}", flush=True)

        message = {"event": event_type, "data": data}
        dead_queues = []

        for queue in queues:
            try:
                queue.put_nowait(message)
            except asyncio.QueueFull:
                dead_queues.append(queue)

        for queue in dead_queues:
            self._party_queues[party_id].discard(queue)

    async def event_stream(
        self, party_id: int, queue: asyncio.Queue
    ) -> AsyncGenerator[dict, None]:
        """Yield SSE events as dicts for EventSourceResponse.

        sse-starlette expects dicts with 'event' and 'data' keys.
        """
        try:
            while True:
                message = await queue.get()
                event_dict = {
                    "event": message["event"],
                    "data": json.dumps(message["data"]),
                }
                print(f"[SSE] yielding event='{message['event']}' party={party_id}", flush=True)
                yield event_dict
        except asyncio.CancelledError:
            print(f"[SSE] stream cancelled party={party_id}", flush=True)
        finally:
            self.unsubscribe(party_id, queue)


# Global singleton — shared across the application
event_manager = EventManager()
