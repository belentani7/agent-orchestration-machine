from __future__ import annotations

from datetime import UTC, datetime

from machine.application.ports import AuditSink, EventPublisher, Planner, TaskRepository
from machine.application.worker import Worker
from machine.domain.models import DomainEvent, Task, TaskRequest, TaskStatus, TenantContext
from machine.domain.state_machine import transition
from machine.security.policy import CapabilityPolicy


class Orchestrator:
    def __init__(
        self,
        repository: TaskRepository,
        publisher: EventPublisher,
        audit: AuditSink,
        policy: CapabilityPolicy,
        planner: Planner,
        worker: Worker,
    ) -> None:
        self._repository = repository
        self._publisher = publisher
        self._audit = audit
        self._policy = policy
        self._planner = planner
        self._worker = worker

    def submit(self, context: TenantContext, request: TaskRequest) -> Task:
        self._policy.assert_budget_allowed(request.max_budget_usd)
        task = Task(
            tenant_id=context.tenant_id,
            actor_id=context.actor_id,
            capability=request.capability,
            payload=request.payload,
            max_budget_usd=request.max_budget_usd,
        )
        self._repository.save(task)
        self._emit("task.created", task, {"capability": request.capability})
        try:
            transition(task, TaskStatus.PLANNED)
            plan = self._planner.plan(task)
            self._repository.save(task)
            self._emit("task.planned", task, {"steps": len(plan)})

            transition(task, TaskStatus.RUNNING)
            self._repository.save(task)
            self._emit("task.running", task, {})

            outputs: list[dict[str, object]] = []
            step_budget = task.max_budget_usd / len(plan)
            for step in plan:
                outputs.append(self._worker.execute(context, step, step_budget))
                self._emit("step.succeeded", task, {"position": step.position, "capability": step.capability})

            task.result = {"outputs": outputs}
            transition(task, TaskStatus.SUCCEEDED)
            self._repository.save(task)
            self._emit("task.succeeded", task, {"output_count": len(outputs)})
        except Exception as error:
            if task.status not in {TaskStatus.SUCCEEDED, TaskStatus.FAILED, TaskStatus.CANCELLED}:
                transition(task, TaskStatus.FAILED)
            task.error = str(error)
            self._repository.save(task)
            self._emit("task.failed", task, {"error_type": type(error).__name__})
        return task

    def _emit(self, name: str, task: Task, payload: dict[str, object]) -> None:
        event = DomainEvent(
            name=name,
            tenant_id=task.tenant_id,
            task_id=task.id,
            occurred_at=datetime.now(UTC),
            payload=payload,
        )
        self._publisher.publish(event)
        self._audit.record(event)
