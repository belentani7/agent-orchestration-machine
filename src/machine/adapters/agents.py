from __future__ import annotations

from machine.adapters.llm import LLMRouter
from machine.domain.models import TenantContext


class HealthCheckAgent:
    capability = "health.check"

    def execute(self, context: TenantContext, payload: dict[str, object], budget_usd: float) -> dict[str, object]:
        return {"status": "ok", "tenant_id": context.tenant_id, "component": "orchestrator-core"}


class TextInferenceAgent:
    capability = "text.infer"

    def __init__(self, router: LLMRouter) -> None:
        self._router = router

    def execute(self, context: TenantContext, payload: dict[str, object], budget_usd: float) -> dict[str, object]:
        prompt = str(payload.get("prompt", ""))
        if not prompt.strip():
            raise ValueError("El campo payload.prompt es obligatorio")
        response = self._router.generate(prompt, budget_usd)
        return {
            "provider": response.provider,
            "model": response.model,
            "text": response.text,
            "estimated_cost_usd": response.estimated_cost_usd,
        }
