from __future__ import annotations

from dataclasses import dataclass

from agent.llm.base import BaseLLMClient
from agent.memory.semantic import SemanticMemory
from agent.skills.base import AgentContext


@dataclass(frozen=True)
class RememberSkill:
    name: str = "remember"
    description: str = "Mémorise une info: /remember cle=valeur"

    def __init__(self, memory: SemanticMemory):
        object.__setattr__(self, "_memory", memory)

    def run(self, *, args: str, ctx: AgentContext, llm: BaseLLMClient) -> str:
        raw = (args or "").strip()
        if not raw:
            return "Usage: /remember cle=valeur"

        if "=" not in raw:
            return "Format attendu: /remember cle=valeur"

        key, value = raw.split("=", 1)
        key = key.strip()
        value = value.strip()
        if not key or not value:
            return "Format attendu: /remember cle=valeur"

        self._memory.put(key, value)
        return f"OK, mémorisé: {key}={value}"

