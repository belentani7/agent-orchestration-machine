from __future__ import annotations

from dataclasses import dataclass
from math import isfinite
from sys import float_info

from machine.domain.models import TenantContext


class AuthorizationDenied(PermissionError):
    pass


def _valid_budget(value: object) -> bool:
    """Accept only positive finite int/float amounts without coercing bool or huge ints."""
    # Bounds are checked before isfinite: converting a huge int to float raises
    # OverflowError, and bool is a subclass of int in Python.
    return type(value) in (int, float) and 0 < value <= float_info.max and isfinite(value)


@dataclass(frozen=True, slots=True)
class CapabilityPolicy:
    allowed_capabilities: frozenset[str]
    max_task_budget_usd: float

    def __post_init__(self) -> None:
        if not _valid_budget(self.max_task_budget_usd):
            raise ValueError("El presupuesto máximo debe ser un valor finito y positivo")

    def assert_context_valid(self, context: TenantContext) -> None:
        """Reject unauthenticated or malformed principals before storing tasks."""
        if (
            not isinstance(context.tenant_id, str)
            or not context.tenant_id.strip()
            or not isinstance(context.actor_id, str)
            or not context.actor_id.strip()
        ):
            raise AuthorizationDenied("El contexto de tenant y actor es obligatorio")

    def assert_capability_allowed(self, context: TenantContext, capability: str) -> None:
        self.assert_context_valid(context)
        if capability not in self.allowed_capabilities:
            raise AuthorizationDenied(f"Capacidad denegada por política: {capability}")

    def assert_budget_allowed(self, requested_budget_usd: float) -> None:
        if not _valid_budget(requested_budget_usd) or requested_budget_usd > self.max_task_budget_usd:
            raise AuthorizationDenied("El presupuesto solicitado no cumple la política")
