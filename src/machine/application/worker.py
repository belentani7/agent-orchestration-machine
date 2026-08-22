from __future__ import annotations

from machine.application.registry import AgentRegistry
from machine.domain.models import ExecutionStep, TenantContext
from machine.security.policy import CapabilityPolicy


class Worker:
    def __init__(self, registry: AgentRegistry, policy: CapabilityPolicy) -> None:
        self._registry = registry
        self._policy = policy

    def execute(self, context: TenantContext, step: ExecutionStep, budget_usd: float) -> dict[str, object]:
        self._policy.assert_capability_allowed(context, step.capability)
        agent = self._registry.resolve(step.capability)
        return agent.execute(context, step.payload, budget_usd)
