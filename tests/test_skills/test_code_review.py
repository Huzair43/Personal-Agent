import os
import tempfile
import unittest
from pathlib import Path

from agent.config import Config
from agent.llm.base import LLMMessage
from agent.memory.semantic import SemanticMemory
from agent.skills.base import AgentContext
from agent.skills.code_review import CodeReviewSkill, _resolve_review_input


class _FakeLLM:
    def __init__(self) -> None:
        self.last_messages: list[LLMMessage] | None = None

    def chat(self, messages: list[LLMMessage], *, temperature=None) -> str:  # noqa: ANN001
        self.last_messages = messages
        return "reviewed"


class TestCodeReviewSkill(unittest.TestCase):
    def test_resolve_file_input(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            cwd = os.getcwd()
            try:
                os.chdir(td)
                Path("x.txt").write_text("hello", encoding="utf-8")
                title, content = _resolve_review_input("x.txt")
            finally:
                os.chdir(cwd)
        self.assertIn("Fichier:", title)
        self.assertTrue(content.startswith("```text"))

    def test_run_text_input_calls_llm(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            llm = _FakeLLM()
            skill = CodeReviewSkill()
            ctx = AgentContext(user_id="u", config=Config(memory_dir=td))
            out = skill.run(args="print('hi')", ctx=ctx, llm=llm)
            self.assertEqual(out, "reviewed")
            self.assertIsNotNone(llm.last_messages)

