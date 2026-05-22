from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable


SCHEMA_VERSION = 1


@dataclass(frozen=True)
class StoredEvent:
    id: int
    ts: float
    user_id: str
    user_text: str
    agent_text: str


class AgentDB:
    def __init__(self, path: Path):
        self._path = path
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._init()

    @staticmethod
    def from_dir(memory_dir: str) -> "AgentDB":
        return AgentDB(Path(memory_dir) / "agent_data.sqlite3")

    def connect(self) -> sqlite3.Connection:
        con = sqlite3.connect(self._path)
        con.row_factory = sqlite3.Row
        return con

    def _init(self) -> None:
        with self.connect() as con:
            con.execute("PRAGMA journal_mode=WAL;")
            con.execute("PRAGMA synchronous=NORMAL;")
            con.execute(
                """
                CREATE TABLE IF NOT EXISTS meta (
                  key TEXT PRIMARY KEY,
                  value TEXT NOT NULL
                )
                """
            )
            con.execute(
                """
                CREATE TABLE IF NOT EXISTS events (
                  id INTEGER PRIMARY KEY AUTOINCREMENT,
                  ts REAL NOT NULL,
                  user_id TEXT NOT NULL,
                  user_text TEXT NOT NULL,
                  agent_text TEXT NOT NULL
                )
                """
            )
            con.execute("CREATE INDEX IF NOT EXISTS idx_events_user_ts ON events(user_id, ts)")
            con.execute("CREATE INDEX IF NOT EXISTS idx_events_ts ON events(ts)")
            con.execute(
                """
                CREATE TABLE IF NOT EXISTS habits_daily (
                  day TEXT PRIMARY KEY,
                  user_id TEXT NOT NULL,
                  stats_json TEXT NOT NULL,
                  created_ts REAL NOT NULL
                )
                """
            )
            con.execute(
                """
                CREATE TABLE IF NOT EXISTS suggestions (
                  id INTEGER PRIMARY KEY AUTOINCREMENT,
                  ts REAL NOT NULL,
                  user_id TEXT NOT NULL,
                  payload_json TEXT NOT NULL
                )
                """
            )
            con.execute("INSERT OR IGNORE INTO meta(key,value) VALUES('schema_version', ?)", (str(SCHEMA_VERSION),))

    def insert_event(self, *, ts: float, user_id: str, user_text: str, agent_text: str) -> int:
        with self.connect() as con:
            cur = con.execute(
                "INSERT INTO events(ts,user_id,user_text,agent_text) VALUES(?,?,?,?)",
                (float(ts), str(user_id), str(user_text), str(agent_text)),
            )
            return int(cur.lastrowid)

    def recent_events(self, *, user_id: str, limit: int = 50) -> list[StoredEvent]:
        with self.connect() as con:
            rows = con.execute(
                "SELECT id, ts, user_id, user_text, agent_text FROM events WHERE user_id=? ORDER BY ts DESC LIMIT ?",
                (user_id, int(limit)),
            ).fetchall()
        out: list[StoredEvent] = []
        for r in rows:
            out.append(
                StoredEvent(
                    id=int(r["id"]),
                    ts=float(r["ts"]),
                    user_id=str(r["user_id"]),
                    user_text=str(r["user_text"]),
                    agent_text=str(r["agent_text"]),
                )
            )
        return out

    def count_events(self, *, user_id: str | None = None) -> int:
        with self.connect() as con:
            if user_id is None:
                row = con.execute("SELECT COUNT(*) AS n FROM events").fetchone()
            else:
                row = con.execute("SELECT COUNT(*) AS n FROM events WHERE user_id=?", (user_id,)).fetchone()
        return int(row["n"]) if row else 0

    def upsert_daily_habits(self, *, day: str, user_id: str, stats: dict[str, Any], created_ts: float) -> None:
        with self.connect() as con:
            con.execute(
                """
                INSERT INTO habits_daily(day, user_id, stats_json, created_ts)
                VALUES(?,?,?,?)
                ON CONFLICT(day) DO UPDATE SET
                  user_id=excluded.user_id,
                  stats_json=excluded.stats_json,
                  created_ts=excluded.created_ts
                """,
                (day, user_id, json.dumps(stats, ensure_ascii=False), float(created_ts)),
            )

    def insert_suggestion(self, *, ts: float, user_id: str, payload: dict[str, Any]) -> int:
        with self.connect() as con:
            cur = con.execute(
                "INSERT INTO suggestions(ts,user_id,payload_json) VALUES(?,?,?)",
                (float(ts), str(user_id), json.dumps(payload, ensure_ascii=False)),
            )
            return int(cur.lastrowid)

    def latest_suggestions(self, *, user_id: str, limit: int = 5) -> list[dict[str, Any]]:
        with self.connect() as con:
            rows = con.execute(
                "SELECT payload_json FROM suggestions WHERE user_id=? ORDER BY ts DESC LIMIT ?",
                (user_id, int(limit)),
            ).fetchall()
        out: list[dict[str, Any]] = []
        for r in rows:
            try:
                out.append(json.loads(str(r["payload_json"])))
            except Exception:
                continue
        return out


def iter_jsonl(path: Path) -> Iterable[dict[str, Any]]:
    if not path.exists():
        return []
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            yield json.loads(line)
        except Exception:
            continue

