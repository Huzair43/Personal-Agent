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
from agent.skills.doc_summarizer import DocSummarizerSkill
from agent.skills.git_helper import GitHelperSkill
from agent.skills.recall import RecallSkill
from agent.skills.remember import RememberSkill
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
        skills: list[Skill] = [
            TasksPlannerSkill(),
            CodeReviewSkill(),
            DocSummarizerSkill(),
            GitHelperSkill(),
            RememberSkill(semantic),
            RecallSkill(semantic),
        ]
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

        messages = list(self._default_prompt(text, user_id=user_id))
        reply = self.llm.chat(messages)
        self.episodic_memory.add_event(user_id=user_id, user_text=text, agent_text=reply)
        return reply

    def _find_skill(self, name: str) -> Skill | None:
        for skill in self.skills:
            if skill.name == name:
                return skill
        return None

    def _default_prompt(self, user_text: str, *, user_id: str) -> Iterable[LLMMessage]:
        system = (
            "Tu es un assistant local. Réponds en français de façon concise.\n"
            "Si l'utilisateur demande un plan, propose une liste d'étapes.\n"
            "Commandes: /help, /plan, /review, /doc, /git, /remember, /recall."
        )
        yield LLMMessage(role=LLMRole.SYSTEM, content=system)
        ctx = self._memory_context(user_id=user_id, query=user_text)
        if ctx:
            yield LLMMessage(role=LLMRole.SYSTEM, content=ctx)
        yield LLMMessage(role=LLMRole.USER, content=user_text)

    def _memory_context(self, *, user_id: str, query: str) -> str:
        """
        Adds lightweight context from episodic + semantic memory.
        Keep it short to avoid polluting the prompt.
        """
        parts: list[str] = []

        recent = self.episodic_memory.tail(10)
        if recent:
            lines: list[str] = []
            for ev in recent:
                if ev.user_id != user_id:
                    continue
                u = (ev.user_text or "").replace("\n", " ").strip()
                a = (ev.agent_text or "").replace("\n", " ").strip()
                if not u or not a:
                    continue
                lines.append(f"U: {u}")
                lines.append(f"A: {a}")
            if lines:
                parts.append("Contexte récent:\n" + "\n".join(lines[-12:]))

        hits = self.semantic_memory.search(query, limit=5)
        if hits:
            parts.append("Rappels:\n" + "\n".join(f"{h.key}={h.value}" for h in hits))

        return "\n\n".join(parts).strip()
