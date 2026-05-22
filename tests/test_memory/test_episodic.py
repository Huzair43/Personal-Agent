import tempfile
import unittest

from agent.memory.episodic import EpisodicMemory


class TestEpisodicMemory(unittest.TestCase):
    def test_add_and_tail(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            mem = EpisodicMemory.from_dir(td)
            mem.add_event(user_id="u", user_text="hi", agent_text="yo")
            mem.add_event(user_id="u", user_text="a", agent_text="b")
            tail = mem.tail(10)
            self.assertGreaterEqual(len(tail), 2)
            self.assertEqual(tail[-1].agent_text, "b")

