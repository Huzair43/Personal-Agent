from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from agent.config import Config
from agent.llm.base import LLMMessage, LLMRole, BaseLLMClient
from agent.llm.ollama_client import OllamaClient
from agent.memory.episodic import EpisodicMemory
from agent.memory.semantic import SemanticMemory
from agent.skills.base import AgentContext, Skill
from agent.skills.code_review import CodeReviewSkill
from agent.skills.git_helper import GitHelperSkill
from agent.skills.tasks_planner import TasksPlannerSkill


@dataclass
class AgentCore:
    config: Config
    llm: BaseLLMClient
    episodic_memory: EpisodicMemory
    semantic_memory: SemanticMemory
    skills: list[Skill]

    @staticmethod
    def default() -> "AgentCore":
        config = Config.load()
        llm = OllamaClient(host=config.ollama_host, model=config.ollama_model)
        episodic = EpisodicMemory.from_dir(config.memory_dir)
        semantic = SemanticMemory.from_dir(config.memory_dir)
        skills: list[Skill] = [TasksPlannerSkill(), CodeReviewSkill(), GitHelperSkill()]
        return AgentCore(
            config=config,
            llm=llm,
            episodic_memory=episodic,
            semantic_memory=semantic,
            skills=skills,
        )

    def list_commands(self) -> str:
        lines = ["Commandes disponibles:"]
        for skill in self.skills:
            lines.append(f"/{skill.name}: {skill.description}")
        return "\n".join(lines)

    def handle_message(self, text: str, *, user_id: str = "local") -> str:
        text = (text or "").strip()
        if not text:
            return "Message vide."

        if text in {"/help", "help"}:
            return self.list_commands()

        if text.startswith("/"):
            cmd, *rest = text[1:].split()
            args = " ".join(rest).strip()
            skill = self._find_skill(cmd)
            if skill is None:
                return f"Commande inconnue: /{cmd}\n\n{self.list_commands()}"
            ctx = AgentContext(user_id=user_id, config=self.config)
            result = skill.run(args=args, ctx=ctx, llm=self.llm)
            self.episodic_memory.add_event(user_id=user_id, user_text=text, agent_text=result)
            return result

        messages = list(self._default_prompt(text))
        reply = self.llm.chat(messages)
        self.episodic_memory.add_event(user_id=user_id, user_text=text, agent_text=reply)
        return reply

    def _find_skill(self, name: str) -> Skill | None:
        for skill in self.skills:
            if skill.name == name:
                return skill
        return None

    def _default_prompt(self, user_text: str) -> Iterable[LLMMessage]:
        system = (
            "Tu es un assistant local. Réponds en français de façon concise.\n"
            "Si l'utilisateur demande un plan, propose une liste d'étapes.\n"
            "Commandes: /help, /plan, /review, /git."
        )
        yield LLMMessage(role=LLMRole.SYSTEM, content=system)
        yield LLMMessage(role=LLMRole.USER, content=user_text)
