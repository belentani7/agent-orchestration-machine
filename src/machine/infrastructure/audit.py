from __future__ import annotations

from dataclasses import asdict

from machine.domain.models import DomainEvent


class InMemoryAuditLog:
    def __init__(self) -> None:
        self._records: list[dict[str, object]] = []

    def record(self, event: DomainEvent) -> None:
        record = asdict(event)
        record["occurred_at"] = event.occurred_at.isoformat()
        self._records.append(record)

    def records_for(self, tenant_id: str, task_id: str) -> list[dict[str, object]]:
        return [
            record for record in self._records
            if record["tenant_id"] == tenant_id and record["task_id"] == task_id
        ]
