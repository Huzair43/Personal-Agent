from __future__ import annotations

import datetime as dt
import os
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from apscheduler.schedulers.background import BackgroundScheduler
from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

from agent.config import Config
from agent.storage.db import AgentDB
from daemon.habits import compute_daily_habits, compute_week_profile
from daemon.ingest import EpisodicIngestor


@dataclass(frozen=True)
class SchedulerOptions:
    user_id: str = "local"


class _JsonlChangeHandler(FileSystemEventHandler):
    def __init__(self, on_change: Callable[[], None]):
        self._on_change = on_change

    def on_modified(self, event):  # noqa: ANN001
        if event.is_directory:
            return
        self._on_change()

    def on_created(self, event):  # noqa: ANN001
        if event.is_directory:
            return
        self._on_change()


@dataclass
class SchedulerHandle:
    scheduler: BackgroundScheduler
    observer: Observer

    def stop(self) -> None:
        try:
            self.observer.stop()
            self.observer.join(timeout=5)
        except Exception:
            pass
        try:
            self.scheduler.shutdown(wait=False)
        except Exception:
            pass


def start_scheduler(cfg: Config | None = None, *, user_id: str | None = None) -> SchedulerHandle:
    cfg = cfg or Config.load()
    db = AgentDB(Path(cfg.db_path)) if cfg.db_path else AgentDB.from_dir(cfg.memory_dir)

    opts = SchedulerOptions(user_id=user_id or os.getenv("SCHED_USER_ID", "local"))
    jsonl_path = Path(cfg.memory_dir) / "episodic.jsonl"
    ingestor = EpisodicIngestor(db, jsonl_path)

    ingest_seconds = float(os.getenv("SCHED_INGEST_SECONDS", "3600"))
    daily_minutes = float(os.getenv("SCHED_DAILY_MINUTES", "60"))
    week_minutes = float(os.getenv("SCHED_WEEK_MINUTES", "60"))
    enable_watch = (os.getenv("SCHED_WATCH") or "0") == "1"

    def ingest_job() -> None:
        ingestor.ingest_new()

    def daily_job() -> None:
        today = dt.date.today()
        stats = compute_daily_habits(db, user_id=opts.user_id, day=today)
        db.upsert_daily_habits(day=today.isoformat(), user_id=opts.user_id, stats=stats, created_ts=time.time())

    def week_job() -> None:
        profile = compute_week_profile(db, user_id=opts.user_id, days=7)
        db.insert_suggestion(ts=time.time(), user_id=opts.user_id, payload={"type": "week_profile", "data": profile})

    scheduler = BackgroundScheduler()
    scheduler.add_job(ingest_job, "interval", seconds=max(1.0, ingest_seconds), id="ingest")
    scheduler.add_job(daily_job, "interval", minutes=max(1.0, daily_minutes), id="daily_stats")
    scheduler.add_job(week_job, "interval", minutes=max(1.0, week_minutes), id="week_profile")
    scheduler.start()

    observer = Observer()
    if enable_watch:
        handler = _JsonlChangeHandler(on_change=ingest_job)
        watch_dir = jsonl_path.parent if jsonl_path.parent.exists() else Path(cfg.memory_dir)
        watch_dir.mkdir(parents=True, exist_ok=True)
        observer.schedule(handler, str(watch_dir), recursive=False)
        observer.start()

    return SchedulerHandle(scheduler=scheduler, observer=observer)


def main() -> None:
    handle = start_scheduler()
    print("Scheduler actif. Ctrl+C pour arrêter.")
    try:
        while True:
            time.sleep(1.0)
    except KeyboardInterrupt:
        pass
    finally:
        handle.stop()


if __name__ == "__main__":
    main()
