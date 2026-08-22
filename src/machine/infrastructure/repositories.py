from __future__ import annotations

from machine.domain.models import Task


class TaskNotFound(KeyError):
    pass


class TenantIsolationViolation(PermissionError):
    pass


class InMemoryTaskRepository:
    def __init__(self) -> None:
        self._tasks: dict[str, Task] = {}

    def save(self, task: Task) -> None:
        if not task.tenant_id:
            raise TenantIsolationViolation("No se permite persistir una tarea sin tenant")
        existing = self._tasks.get(task.id)
        if existing and existing.tenant_id != task.tenant_id:
            raise TenantIsolationViolation("No se permite cambiar el tenant de una tarea")
        self._tasks[task.id] = task

    def get(self, tenant_id: str, task_id: str) -> Task:
        try:
            task = self._tasks[task_id]
        except KeyError as error:
            raise TaskNotFound(task_id) from error
        if task.tenant_id != tenant_id:
            raise TenantIsolationViolation("Acceso cruzado entre tenants denegado")
        return task
