from __future__ import annotations

from machine.domain.models import ExecutionStep, Task


class DirectPlanner:
    """Planificador inicial: una solicitud autorizada se convierte en un paso explícito."""

    def plan(self, task: Task) -> list[ExecutionStep]:
        return [ExecutionStep(position=1, capability=task.capability, payload=task.payload)]
