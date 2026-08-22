from __future__ import annotations

from typing import Protocol

from machine.domain.models import DomainEvent, ExecutionStep, Task, TenantContext


class TaskRepository(Protocol):
    def save(self, task: Task) -> None: ...
    def get(self, tenant_id: str, task_id: str) -> Task: ...


class EventPublisher(Protocol):
    def publish(self, event: DomainEvent) -> None: ...


class AuditSink(Protocol):
    def record(self, event: DomainEvent) -> None: ...


class Agent(Protocol):
    capability: str
    def execute(self, context: TenantContext, payload: dict[str, object], budget_usd: float) -> dict[str, object]: ...


class Planner(Protocol):
    def plan(self, task: Task) -> list[ExecutionStep]: ...
