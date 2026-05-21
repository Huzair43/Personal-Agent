from __future__ import annotations

from dataclasses import dataclass

from agent.llm.base import LLMMessage, LLMRole, BaseLLMClient
from agent.skills.base import AgentContext


@dataclass(frozen=True)
class CodeReviewSkill:
    name: str = "review"
    description: str = "Donne un avis rapide sur un extrait de code."

    def run(self, *, args: str, ctx: AgentContext, llm: BaseLLMClient) -> str:
        if not args.strip():
            return "Usage: /review <colle ici ton code ou un résumé du changement>"

        messages = [
            LLMMessage(role=LLMRole.SYSTEM, content="Tu fais une revue de code concise en français."),
            LLMMessage(role=LLMRole.USER, content=args),
        ]
        return llm.chat(messages)

