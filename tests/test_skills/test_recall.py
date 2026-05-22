import tempfile
import unittest

from agent.config import Config
from agent.memory.semantic import SemanticMemory
from agent.skills.base import AgentContext
from agent.skills.recall import RecallSkill


class _NoLLM:
    def chat(self, messages, *, temperature=None):  # noqa: ANN001
        raise AssertionError("LLM should not be called for recall")


class TestRecallSkill(unittest.TestCase):
    def test_recall_reads_semantic(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            mem = SemanticMemory.from_dir(td)
            mem.put("city", "Paris")
            skill = RecallSkill(mem)
            ctx = AgentContext(user_id="u", config=Config(memory_dir=td))
            out = skill.run(args="cit", ctx=ctx, llm=_NoLLM())
            self.assertIn("city=Paris", out)

