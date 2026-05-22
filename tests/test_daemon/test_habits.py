import datetime as dt
import tempfile
import unittest
from pathlib import Path

from agent.storage.db import AgentDB
from daemon.habits import compute_daily_habits, compute_week_profile


class TestHabits(unittest.TestCase):
    def test_daily_habits(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            db = AgentDB(Path(td) / "x.sqlite3")
            day = dt.date.today()
            ts = dt.datetime.combine(day, dt.time(hour=10)).timestamp()
            db.insert_event(ts=ts, user_id="u", user_text="/git status", agent_text="ok")
            db.insert_event(ts=ts + 60, user_id="u", user_text="hello", agent_text="ok")
            stats = compute_daily_habits(db, user_id="u", day=day)
            self.assertEqual(stats["total_messages"], 2)
            self.assertIn("10", stats["top_hours"])
            self.assertIn("git", stats["top_commands"])

    def test_week_profile(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            db = AgentDB(Path(td) / "x.sqlite3")
            day = dt.date.today()
            ts = dt.datetime.combine(day, dt.time(hour=9)).timestamp()
            db.insert_event(ts=ts, user_id="u", user_text="/help", agent_text="ok")
            profile = compute_week_profile(db, user_id="u", end_day=day, days=7)
            self.assertEqual(profile["user_id"], "u")
            self.assertTrue(profile["messages_per_day"])

