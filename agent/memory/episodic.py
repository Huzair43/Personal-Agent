from __future__ import annotations

import json
import time
from dataclasses import dataclass
from pathlib import Path

from filelock import FileLock


@dataclass(frozen=True)
class EpisodicEvent:
    ts: float
    user_id: str
    user_text: str
    agent_text: str


class EpisodicMemory:
    def __init__(self, path: Path):
        self._path = path
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = FileLock(str(self._path) + ".lock")

    @staticmethod
    def from_dir(memory_dir: str) -> "EpisodicMemory":
        return EpisodicMemory(Path(memory_dir) / "episodic.jsonl")

    def add_event(self, *, user_id: str, user_text: str, agent_text: str) -> None:
        event = EpisodicEvent(ts=time.time(), user_id=user_id, user_text=user_text, agent_text=agent_text)
        with self._lock:
            with self._path.open("a", encoding="utf-8") as f:
                f.write(json.dumps(event.__dict__, ensure_ascii=False) + "\n")

    def tail(self, n: int = 20) -> list[EpisodicEvent]:
        if not self._path.exists():
            return []
        with self._lock:
            lines = self._path.read_text(encoding="utf-8", errors="replace").splitlines()[-n:]
        out: list[EpisodicEvent] = []
        for line in lines:
            try:
                d = json.loads(line)
                out.append(
                    EpisodicEvent(
                        ts=float(d.get("ts", 0)),
                        user_id=str(d.get("user_id", "")),
                        user_text=str(d.get("user_text", "")),
                        agent_text=str(d.get("agent_text", "")),
                    )
                )
            except Exception:
                continue
        return out
