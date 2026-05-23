from __future__ import annotations

from dataclasses import dataclass

from agent.llm.base import BaseLLMClient
from agent.skills.base import AgentContext


@dataclass(frozen=True)
class LLMInfoSkill:
    name: str = "llm"
    description: str = "Affiche le provider et le modele LLM"

    def run(self, *, args: str, ctx: AgentContext, llm: BaseLLMClient) -> str:
        cfg = ctx.config
        provider = (cfg.llm_provider or "gemini").strip().lower()
        lines: list[str] = []
        lines.append(f"llm_provider: {provider}")
        lines.append(f"gemini_model: {cfg.gemini_model}")
        lines.append(f"gemini_api_key_present: {bool(cfg.gemini_api_key)}")
        return "\n".join(lines)

