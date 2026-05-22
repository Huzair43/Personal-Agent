import tempfile
import unittest

from agent.memory.semantic import SemanticMemory


class TestSemanticMemory(unittest.TestCase):
    def test_put_get_search(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            mem = SemanticMemory.from_dir(td)
            mem.put("name", "Alice")
            self.assertEqual(mem.get("name"), "Alice")
            hits = mem.search("ali", limit=5)
            self.assertTrue(any(h.key == "name" for h in hits))

