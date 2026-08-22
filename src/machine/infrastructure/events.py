from __future__ import annotations

from collections.abc import Callable

from machine.domain.models import DomainEvent


class InMemoryEventBus:
    def __init__(self) -> None:
        self.events: list[DomainEvent] = []
        self._subscribers: list[Callable[[DomainEvent], None]] = []

    def subscribe(self, callback: Callable[[DomainEvent], None]) -> None:
        self._subscribers.append(callback)

    def publish(self, event: DomainEvent) -> None:
        self.events.append(event)
        for callback in self._subscribers:
            callback(event)
