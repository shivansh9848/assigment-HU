
from __future__ import annotations

import asyncio
from collections import defaultdict
from typing import Any, Dict, Set


class EventBroker:
    def __init__(self) -> None:
        # Map run_id -> set of subscriber queues
        self._subscribers: Dict[str, Set[asyncio.Queue]] = defaultdict(set)
        self._lock = asyncio.Lock()

    async def subscribe(self, run_id: str) -> asyncio.Queue:
        queue: asyncio.Queue = asyncio.Queue()
        async with self._lock:
            self._subscribers[run_id].add(queue)
        return queue

    async def unsubscribe(self, run_id: str, queue: asyncio.Queue) -> None:
        async with self._lock:
            if queue in self._subscribers.get(run_id, set()):
                self._subscribers[run_id].remove(queue)
            if not self._subscribers.get(run_id):
                self._subscribers.pop(run_id, None)

    async def publish(self, run_id: str, event: dict[str, Any]) -> None:
        async with self._lock:
            queues = list(self._subscribers.get(run_id, []))
        for q in queues:
            await q.put(event)


broker = EventBroker()
