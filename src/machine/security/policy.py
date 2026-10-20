from __future__ import annotations

from dataclasses import dataclass
from math import isfinite

from machine.domain.models import TenantContext


class AuthorizationDenied(PermissionError):
    pass


@dataclass(frozen=True, slots=True)
class CapabilityPolicy:
    allowed_capabilities: frozenset[str]
    max_task_budget_usd: float

    def __post_init__(self) -> None:
        if not isfinite(self.max_task_budget_usd) or self.max_task_budget_usd <= 0:
            raise ValueError("El presupuesto máximo debe ser un valor finito y positivo")

    def assert_capability_allowed(self, context: TenantContext, capability: str) -> None:
        if not context.tenant_id.strip() or not context.actor_id.strip():
            raise AuthorizationDenied("El contexto de tenant y actor es obligatorio")
        if capability not in self.allowed_capabilities:
            raise AuthorizationDenied(f"Capacidad denegada por política: {capability}")

    def assert_budget_allowed(self, requested_budget_usd: float) -> None:
        if not isfinite(requested_budget_usd) or requested_budget_usd <= 0 or requested_budget_usd > self.max_task_budget_usd:
            raise AuthorizationDenied("El presupuesto solicitado no cumple la política")
