import tempfile
import unittest

from agent.config import Config
from agent.memory.semantic import SemanticMemory
from agent.skills.base import AgentContext
from agent.skills.remember import RememberSkill


class _NoLLM:
    def chat(self, messages, *, temperature=None):  # noqa: ANN001
        raise AssertionError("LLM should not be called for remember")


class TestRememberSkill(unittest.TestCase):
    def test_remember_writes_semantic(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            mem = SemanticMemory.from_dir(td)
            skill = RememberSkill(mem)
            ctx = AgentContext(user_id="u", config=Config(memory_dir=td))
            out = skill.run(args="k=v", ctx=ctx, llm=_NoLLM())
            self.assertIn("OK", out)
            self.assertEqual(mem.get("k"), "v")

