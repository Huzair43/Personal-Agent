from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from filelock import FileLock

from agent.storage.db import AgentDB


@dataclass(frozen=True)
class IngestState:
    offset_bytes: int = 0


class EpisodicIngestor:
    def __init__(self, db: AgentDB, jsonl_path: Path):
        self._db = db
        self._path = jsonl_path
        self._state_path = jsonl_path.with_suffix(".offset")
        self._lock = FileLock(str(self._path) + ".lock")
        self._offset = self._load_offset()

    def ingest_new(self) -> int:
        if not self._path.exists():
            return 0

        inserted = 0
        with self._lock:
            with self._path.open("rb") as f:
                f.seek(self._offset)
                for raw in f:
                    self._offset += len(raw)
                    line = raw.decode("utf-8", errors="replace").strip()
                    if not line:
                        continue
                    try:
                        d = json.loads(line)
                    except Exception:
                        continue
                    try:
                        ts = float(d.get("ts", 0.0))
                        user_id = str(d.get("user_id", "local"))
                        user_text = str(d.get("user_text", ""))
                        agent_text = str(d.get("agent_text", ""))
                    except Exception:
                        continue
                    if not user_text and not agent_text:
                        continue
                    self._db.insert_event(ts=ts, user_id=user_id, user_text=user_text, agent_text=agent_text)
                    inserted += 1

        self._save_offset()
        return inserted

    def reset(self) -> None:
        self._offset = 0
        self._save_offset()

    def _load_offset(self) -> int:
        try:
            return int(self._state_path.read_text(encoding="utf-8").strip())
        except Exception:
            return 0

    def _save_offset(self) -> None:
        try:
            self._state_path.write_text(str(self._offset), encoding="utf-8")
        except Exception:
            return
