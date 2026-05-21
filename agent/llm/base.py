from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Protocol


class LLMRole(str, Enum):
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"


@dataclass(frozen=True)
class LLMMessage:
    role: LLMRole
    content: str


class BaseLLMClient(Protocol):
    def chat(self, messages: list[LLMMessage], *, temperature: float | None = None) -> str: ...

