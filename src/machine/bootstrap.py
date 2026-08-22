from __future__ import annotations

from machine.adapters.agents import HealthCheckAgent, TextInferenceAgent
from machine.adapters.llm import DeterministicLLMProvider, LLMRouter
from machine.application.orchestrator import Orchestrator
from machine.application.planner import DirectPlanner
from machine.application.registry import AgentRegistry
from machine.application.worker import Worker
from machine.infrastructure.audit import InMemoryAuditLog
from machine.infrastructure.events import InMemoryEventBus
from machine.infrastructure.repositories import InMemoryTaskRepository
from machine.security.policy import CapabilityPolicy


def build_machine() -> tuple[Orchestrator, InMemoryAuditLog, InMemoryTaskRepository]:
    policy = CapabilityPolicy(
        allowed_capabilities=frozenset({"health.check", "text.infer"}),
        max_task_budget_usd=0.05,
    )
    router = LLMRouter([
        DeterministicLLMProvider("local-primary", "deterministic-v1", 0.002),
        DeterministicLLMProvider("local-fallback", "deterministic-v1", 0.004),
    ])
    registry = AgentRegistry()
    registry.register(HealthCheckAgent())
    registry.register(TextInferenceAgent(router))
    audit = InMemoryAuditLog()
    repository = InMemoryTaskRepository()
    bus = InMemoryEventBus()
    worker = Worker(registry, policy)
    return Orchestrator(repository, bus, audit, policy, DirectPlanner(), worker), audit, repository
