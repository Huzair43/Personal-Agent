from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from pathlib import Path

from agent.config import Config
from agent.llm.base import LLMMessage, LLMRole, BaseLLMClient
from agent.llm.gemini_client import GeminiClient
from agent.llm.ollama_client import OllamaClient
from agent.memory.episodic import EpisodicMemory
from agent.memory.semantic import SemanticMemory
from agent.skills.base import AgentContext, Skill
from agent.skills.browser import BrowseSkill
from agent.skills.code_review import CodeReviewSkill
from agent.skills.doc_summarizer import DocSummarizerSkill
from agent.skills.explorer import ExplorerSkill
from agent.skills.git_helper import GitHelperSkill
from agent.skills.habits import HabitsSkill
from agent.skills.llm_info import LLMInfoSkill
from agent.skills.recall import RecallSkill
from agent.skills.remember import RememberSkill
from agent.skills.stats import StatsSkill
from agent.skills.tasks_planner import TasksPlannerSkill
from agent.storage.db import AgentDB


@dataclass
class AgentCore:
    config: Config
    llm: BaseLLMClient
    episodic_memory: EpisodicMemory
    semantic_memory: SemanticMemory
    skills: list[Skill]
    db: AgentDB | None = None

    @staticmethod
    def default() -> "AgentCore":
        config = Config.load()
        llm = _build_llm(config)
        episodic = EpisodicMemory.from_dir(config.memory_dir)
        semantic = SemanticMemory.from_dir(config.memory_dir)
        db = AgentDB(Path(config.db_path)) if config.db_path else AgentDB.from_dir(config.memory_dir)
        skills: list[Skill] = [
            TasksPlannerSkill(),
            CodeReviewSkill(),
            DocSummarizerSkill(),
            GitHelperSkill(),
            ExplorerSkill(),
            BrowseSkill(),
            RememberSkill(semantic),
            RecallSkill(semantic),
            HabitsSkill(),
            LLMInfoSkill(),
            StatsSkill(),
        ]
        return AgentCore(
            config=config,
            llm=llm,
            episodic_memory=episodic,
            semantic_memory=semantic,
            skills=skills,
            db=db,
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
            if self.db is not None:
                try:
                    import time

                    self.db.insert_event(ts=time.time(), user_id=user_id, user_text=text, agent_text=result)
                except Exception:
                    pass
            return result

        messages = list(self._default_prompt(text, user_id=user_id))
        reply = self.llm.chat(messages)
        self.episodic_memory.add_event(user_id=user_id, user_text=text, agent_text=reply)
        if self.db is not None:
            try:
                import time

                self.db.insert_event(ts=time.time(), user_id=user_id, user_text=text, agent_text=reply)
            except Exception:
                pass
        return reply

    def _find_skill(self, name: str) -> Skill | None:
        for skill in self.skills:
            if skill.name == name:
                return skill
        return None

    def _default_prompt(self, user_text: str, *, user_id: str) -> Iterable[LLMMessage]:
        system = (
            "Tu es un assistant local. Réponds en français de façon concise.\n"
            "Tu peux utiliser des notes persistées (mots clés, préférences) et le contexte récent.\n"
            "Si une information utile existe dans les notes, utilise la automatiquement.\n"
            "Si l'utilisateur demande un plan, propose une liste d'étapes.\n"
            "Commandes: /help, /plan, /review, /doc, /git, /remember, /recall, /habits, /stats, /llm."
        )
        yield LLMMessage(role=LLMRole.SYSTEM, content=system)
        ctx = self._memory_context(user_id=user_id, query=user_text)
        if ctx:
            yield LLMMessage(role=LLMRole.SYSTEM, content=ctx)
        yield LLMMessage(role=LLMRole.USER, content=user_text)

    def _memory_context(self, *, user_id: str, query: str) -> str:
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

        hits = self.semantic_memory.search(query, limit=8)
        if hits:
            parts.append("Notes pertinentes:\n" + "\n".join(f"{h.key}={h.value}" for h in hits))
        else:
            items = self.semantic_memory.items(limit=20)
            if items:
                parts.append("Notes connues:\n" + "\n".join(f"{it.key}={it.value}" for it in items))

        return "\n\n".join(parts).strip()


def _build_llm(config: Config) -> BaseLLMClient:
    provider = (config.llm_provider or "ollama").strip().lower()
    if provider == "gemini":
        if not config.gemini_api_key:
            return OllamaClient(host=config.ollama_host, model=config.ollama_model)
        return GeminiClient(api_key=config.gemini_api_key, model=config.gemini_model)
    return OllamaClient(host=config.ollama_host, model=config.ollama_model)
