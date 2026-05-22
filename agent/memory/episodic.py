from __future__ import annotations

import json
import time
from dataclasses import dataclass
from pathlib import Path
from collections import deque

from filelock import FileLock


@dataclass(frozen=True)
class EpisodicEvent:
    ts: float
    user_id: str
    user_text: str
    agent_text: str


class EpisodicMemory:
    def __init__(self, path: Path, cache_size: int = 500):
        self._path = path
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = FileLock(str(self._path) + ".lock")
        self._cache_size = cache_size
        self._events_cache: deque[EpisodicEvent] = deque(maxlen=cache_size)
        self._file_size_last_read = 0
        self._load_initial_cache()

    @staticmethod
    def from_dir(memory_dir: str) -> "EpisodicMemory":
        return EpisodicMemory(Path(memory_dir) / "episodic.jsonl")

    def add_event(self, *, user_id: str, user_text: str, agent_text: str) -> None:
        event = EpisodicEvent(ts=time.time(), user_id=user_id, user_text=user_text, agent_text=agent_text)
        with self._lock:
            with self._path.open("a", encoding="utf-8") as f:
                f.write(json.dumps(event.__dict__, ensure_ascii=False) + "\n")
            self._events_cache.append(event)

    def tail(self, n: int = 20) -> list[EpisodicEvent]:
        if not self._path.exists():
            return []
        
        # Vérifier si le fichier a grandi depuis la dernière lecture
        try:
            current_size = self._path.stat().st_size
            if current_size > self._file_size_last_read:
                self._sync_cache_from_end()
                self._file_size_last_read = current_size
        except OSError:
            pass
        
        # Retourner les n derniers événements du cache
        return list(self._events_cache)[-n:] if self._events_cache else []

    def _load_initial_cache(self) -> None:
        """Charge les derniers événements du fichier au démarrage."""
        if not self._path.exists():
            return
        
        try:
            with self._lock:
                lines = self._path.read_text(encoding="utf-8", errors="replace").splitlines()
                self._file_size_last_read = self._path.stat().st_size
                
                for line in lines[-self._cache_size:]:
                    event = self._parse_line(line)
                    if event:
                        self._events_cache.append(event)
        except Exception:
            pass

    def _sync_cache_from_end(self) -> None:
        """Recharge les derniers événements du fichier (optimisé)."""
        if not self._path.exists():
            return
        
        try:
            with self._lock:
                lines = self._path.read_text(encoding="utf-8", errors="replace").splitlines()
                # Garder seulement les lignes après le cache
                start_idx = max(0, len(lines) - self._cache_size)
                for line in lines[start_idx:]:
                    event = self._parse_line(line)
                    if event:
                        self._events_cache.append(event)
        except Exception:
            pass

    @staticmethod
    def _parse_line(line: str) -> EpisodicEvent | None:
        """Parse une ligne JSON en EpisodicEvent."""
        try:
            d = json.loads(line)
            return EpisodicEvent(
                ts=float(d.get("ts", 0)),
                user_id=str(d.get("user_id", "")),
                user_text=str(d.get("user_text", "")),
                agent_text=str(d.get("agent_text", "")),
            )
        except Exception:
            return None
