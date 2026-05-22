import tempfile
import unittest
from pathlib import Path

from agent.storage.db import AgentDB


class TestAgentDB(unittest.TestCase):
    def test_insert_and_recent(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            db = AgentDB(Path(td) / "x.sqlite3")
            db.insert_event(ts=1.0, user_id="u", user_text="a", agent_text="b")
            db.insert_event(ts=2.0, user_id="u", user_text="c", agent_text="d")
            recent = db.recent_events(user_id="u", limit=10)
            self.assertEqual(len(recent), 2)
            self.assertEqual(recent[0].user_text, "c")
            self.assertEqual(db.count_events(user_id="u"), 2)

