from __future__ import annotations

from machine.application.ports import Agent


class UnknownCapability(KeyError):
    pass


class AgentRegistry:
    def __init__(self) -> None:
        self._agents: dict[str, Agent] = {}

    def register(self, agent: Agent) -> None:
        if agent.capability in self._agents:
            raise ValueError(f"Capacidad duplicada: {agent.capability}")
        self._agents[agent.capability] = agent

    def resolve(self, capability: str) -> Agent:
        try:
            return self._agents[capability]
        except KeyError as error:
            raise UnknownCapability(f"Capacidad no registrada: {capability}") from error

    def capabilities(self) -> tuple[str, ...]:
        return tuple(sorted(self._agents))
