from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True, slots=True)
class LLMResponse:
    provider: str
    model: str
    text: str
    estimated_cost_usd: float


class LLMProvider(Protocol):
    name: str
    estimated_cost_usd: float
    def generate(self, prompt: str) -> LLMResponse: ...


class DeterministicLLMProvider:
    """Proveedor sin red para pruebas; nunca transmite datos fuera de la máquina."""

    def __init__(self, name: str, model: str, estimated_cost_usd: float, enabled: bool = True) -> None:
        self.name = name
        self.model = model
        self.estimated_cost_usd = estimated_cost_usd
        self.enabled = enabled

    def generate(self, prompt: str) -> LLMResponse:
        if not self.enabled:
            raise RuntimeError(f"Proveedor no disponible: {self.name}")
        return LLMResponse(
            provider=self.name,
            model=self.model,
            text=f"Respuesta simulada y local para: {prompt}",
            estimated_cost_usd=self.estimated_cost_usd,
        )


class LLMRouter:
    def __init__(self, providers: list[LLMProvider]) -> None:
        self._providers = sorted(providers, key=lambda item: item.estimated_cost_usd)

    def generate(self, prompt: str, max_budget_usd: float) -> LLMResponse:
        failures: list[str] = []
        for provider in self._providers:
            if provider.estimated_cost_usd > max_budget_usd:
                continue
            try:
                return provider.generate(prompt)
            except Exception as error:
                failures.append(f"{provider.name}: {type(error).__name__}")
        detail = "; ".join(failures) or "sin proveedores dentro de presupuesto"
        raise RuntimeError(f"No fue posible completar inferencia: {detail}")
