from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from agent.config import Config
from agent.llm.base import BaseLLMClient


@dataclass(frozen=True)
class AgentContext:
    user_id: str
    config: Config


class Skill(Protocol):
    name: str
    description: str

    def run(self, *, args: str, ctx: AgentContext, llm: BaseLLMClient) -> str: ...

