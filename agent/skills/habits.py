from __future__ import annotations

import datetime as dt
from dataclasses import dataclass
from pathlib import Path

from agent.config import Config
from agent.llm.base import BaseLLMClient
from agent.storage.db import AgentDB
from daemon.habits import compute_daily_habits, compute_week_profile
from agent.skills.base import AgentContext


@dataclass(frozen=True)
class HabitsSkill:
    name: str = "habits"
    description: str = "Affiche des stats d usage: /habits [today|week]"

    def run(self, *, args: str, ctx: AgentContext, llm: BaseLLMClient) -> str:
        mode = (args or "").strip().lower() or "today"
        cfg: Config = ctx.config
        db = AgentDB(Path(cfg.db_path)) if cfg.db_path else AgentDB.from_dir(cfg.memory_dir)

        if mode in {"today", "jour"}:
            stats = compute_daily_habits(db, user_id=ctx.user_id, day=dt.date.today())
            return _format(stats)

        if mode in {"week", "semaine"}:
            profile = compute_week_profile(db, user_id=ctx.user_id, days=7)
            return _format(profile)

        return "Usage: /habits today | /habits week"


def _format(d: dict) -> str:
    lines: list[str] = []
    for k, v in d.items():
        lines.append(f"{k}: {v}")
    return "\n".join(lines)

