from __future__ import annotations

from dataclasses import dataclass

from agent.llm.base import BaseLLMClient
from agent.memory.semantic import SemanticMemory
from agent.skills.base import AgentContext


@dataclass(frozen=True)
class RecallSkill:
    name: str = "recall"
    description: str = "Recherche dans la mémoire: /recall mot"

    def __init__(self, memory: SemanticMemory):
        object.__setattr__(self, "_memory", memory)

    def run(self, *, args: str, ctx: AgentContext, llm: BaseLLMClient) -> str:
        q = (args or "").strip()
        if not q:
            return "Usage: /recall <mot>"

        hits = self._memory.search(q, limit=10)
        if not hits:
            return "(aucun résultat)"

        lines = ["Résultats:"]
        for h in hits:
            lines.append(f"{h.key}={h.value}")
        return "\n".join(lines)

