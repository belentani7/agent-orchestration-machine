from __future__ import annotations

from datetime import UTC, datetime

from machine.domain.models import Task, TaskStatus


_ALLOWED: dict[TaskStatus, set[TaskStatus]] = {
    TaskStatus.CREATED: {TaskStatus.PLANNED, TaskStatus.CANCELLED, TaskStatus.FAILED},
    TaskStatus.PLANNED: {TaskStatus.RUNNING, TaskStatus.CANCELLED, TaskStatus.FAILED},
    TaskStatus.RUNNING: {TaskStatus.SUCCEEDED, TaskStatus.FAILED, TaskStatus.CANCELLED},
    TaskStatus.SUCCEEDED: set(),
    TaskStatus.FAILED: set(),
    TaskStatus.CANCELLED: set(),
}


class InvalidTaskTransition(ValueError):
    pass


def transition(task: Task, target: TaskStatus) -> Task:
    if target not in _ALLOWED[task.status]:
        raise InvalidTaskTransition(f"Transición no permitida: {task.status.value} -> {target.value}")
    task.status = target
    task.updated_at = datetime.now(UTC)
    return task
