from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from agent.llm.base import BaseLLMClient
from agent.skills.base import AgentContext
from agent.storage.db import AgentDB


@dataclass(frozen=True)
class StatsSkill:
    name: str = "stats"
    description: str = "Etat tracking: /stats"

    def run(self, *, args: str, ctx: AgentContext, llm: BaseLLMClient) -> str:
        cfg = ctx.config
        db = AgentDB(Path(cfg.db_path)) if cfg.db_path else AgentDB.from_dir(cfg.memory_dir)
        total = db.count_events()
        mine = db.count_events(user_id=ctx.user_id)
        sugg = db.latest_suggestions(user_id=ctx.user_id, limit=3)
        lines: list[str] = []
        lines.append(f"events_total: {total}")
        lines.append(f"events_user: {mine}")
        lines.append(f"last_suggestions_count: {len(sugg)}")
        return "\n".join(lines)

