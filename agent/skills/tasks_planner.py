from __future__ import annotations

from dataclasses import dataclass

from agent.llm.base import LLMMessage, LLMRole, BaseLLMClient
from agent.skills.base import AgentContext


@dataclass(frozen=True)
class TasksPlannerSkill:
    name: str = "plan"
    description: str = "Génère un plan d'implémentation."

    def run(self, *, args: str, ctx: AgentContext, llm: BaseLLMClient) -> str:
        topic = args.strip() or "le sujet donné par l'utilisateur"
        messages = [
            LLMMessage(
                role=LLMRole.SYSTEM,
                content="Crée un plan d'implémentation en étapes courtes, en français, sans blabla.",
            ),
            LLMMessage(role=LLMRole.USER, content=topic),
        ]
        return llm.chat(messages)

