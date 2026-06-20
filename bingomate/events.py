from __future__ import annotations

import asyncio
import time
from collections import deque
from dataclasses import asdict, dataclass
from threading import Lock
from typing import Any


@dataclass(frozen=True)
class EventRecord:
    id: int
    kind: str
    payload: dict[str, Any]
    created_at: float


@dataclass(frozen=True)
class EventSubscriber:
    queue: asyncio.Queue[EventRecord]
    loop: asyncio.AbstractEventLoop


class EventBus:
    def __init__(self, max_events: int = 200) -> None:
        self._events: deque[EventRecord] = deque(maxlen=max_events)
        self._subscribers: set[EventSubscriber] = set()
        self._lock = Lock()
        self._next_id = 1

    def publish(self, kind: str, payload: dict[str, Any] | None = None) -> EventRecord:
        with self._lock:
            record = EventRecord(
                id=self._next_id,
                kind=kind,
                payload=payload or {},
                created_at=time.time(),
            )
            self._next_id += 1
            self._events.append(record)
            subscribers = list(self._subscribers)

        for subscriber in subscribers:
            if subscriber.loop.is_closed():
                self.unsubscribe(subscriber)
                continue
            subscriber.loop.call_soon_threadsafe(_put_nowait, subscriber.queue, record)
        return record

    def recent(self, limit: int = 50) -> list[EventRecord]:
        with self._lock:
            return list(self._events)[-limit:]

    def subscribe(self) -> EventSubscriber:
        subscriber = EventSubscriber(asyncio.Queue(maxsize=100), asyncio.get_running_loop())
        with self._lock:
            self._subscribers.add(subscriber)
        return subscriber

    def unsubscribe(self, subscriber: EventSubscriber) -> None:
        with self._lock:
            self._subscribers.discard(subscriber)

    def recent_as_dicts(self, limit: int = 50) -> list[dict[str, Any]]:
        return [asdict(record) for record in self.recent(limit)]


def _put_nowait(queue: asyncio.Queue[EventRecord], record: EventRecord) -> None:
    try:
        queue.put_nowait(record)
    except asyncio.QueueFull:
        _ = queue.get_nowait()
        queue.put_nowait(record)
