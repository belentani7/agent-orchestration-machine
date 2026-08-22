from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any
from uuid import uuid4


class TaskStatus(StrEnum):
    CREATED = "created"
    PLANNED = "planned"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass(frozen=True, slots=True)
class TenantContext:
    tenant_id: str
    actor_id: str
    roles: frozenset[str] = frozenset()


@dataclass(frozen=True, slots=True)
class TaskRequest:
    capability: str
    payload: dict[str, Any]
    max_budget_usd: float = 0.01
    idempotency_key: str | None = None


@dataclass(slots=True)
class Task:
    tenant_id: str
    actor_id: str
    capability: str
    payload: dict[str, Any]
    max_budget_usd: float
    id: str = field(default_factory=lambda: str(uuid4()))
    status: TaskStatus = TaskStatus.CREATED
    result: dict[str, Any] | None = None
    error: str | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    def snapshot(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "tenant_id": self.tenant_id,
            "actor_id": self.actor_id,
            "capability": self.capability,
            "status": self.status.value,
            "result": self.result,
            "error": self.error,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }


@dataclass(frozen=True, slots=True)
class ExecutionStep:
    position: int
    capability: str
    payload: dict[str, Any]


@dataclass(frozen=True, slots=True)
class DomainEvent:
    name: str
    tenant_id: str
    task_id: str
    occurred_at: datetime
    payload: dict[str, Any]
