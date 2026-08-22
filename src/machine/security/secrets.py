from __future__ import annotations

import os
from typing import Protocol


class SecretProvider(Protocol):
    def get(self, reference: str) -> str: ...


class EnvironmentSecretProvider:
    """Adaptador de desarrollo. Producción debe sustituirlo por un gestor dedicado."""

    def get(self, reference: str) -> str:
        value = os.getenv(reference)
        if not value:
            raise KeyError(f"Secreto no disponible: {reference}")
        return value
