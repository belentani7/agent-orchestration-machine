from __future__ import annotations

from dataclasses import dataclass

from machine.domain.models import TenantContext


class AuthorizationDenied(PermissionError):
    pass


@dataclass(frozen=True, slots=True)
class CapabilityPolicy:
    allowed_capabilities: frozenset[str]
    max_task_budget_usd: float

    def assert_capability_allowed(self, context: TenantContext, capability: str) -> None:
        if not context.tenant_id.strip() or not context.actor_id.strip():
            raise AuthorizationDenied("El contexto de tenant y actor es obligatorio")
        if capability not in self.allowed_capabilities:
            raise AuthorizationDenied(f"Capacidad denegada por política: {capability}")

    def assert_budget_allowed(self, requested_budget_usd: float) -> None:
        if requested_budget_usd <= 0 or requested_budget_usd > self.max_task_budget_usd:
            raise AuthorizationDenied("El presupuesto solicitado no cumple la política")
