import tempfile
import unittest

from agent.config import Config
from agent.core import AgentCore
from agent.llm.base import LLMMessage
from agent.memory.episodic import EpisodicMemory
from agent.memory.semantic import SemanticMemory
from agent.skills.code_review import CodeReviewSkill
from agent.skills.doc_summarizer import DocSummarizerSkill
from agent.skills.git_helper import GitHelperSkill
from agent.skills.recall import RecallSkill
from agent.skills.remember import RememberSkill
from agent.skills.tasks_planner import TasksPlannerSkill


class _FakeLLM:
    def __init__(self) -> None:
        self.last_messages: list[LLMMessage] | None = None

    def chat(self, messages: list[LLMMessage], *, temperature=None) -> str:  # noqa: ANN001
        self.last_messages = messages
        return "ok"


class TestAgentCore(unittest.TestCase):
    def test_help_lists_commands(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            cfg = Config(memory_dir=td)
            llm = _FakeLLM()
            episodic = EpisodicMemory.from_dir(td)
            semantic = SemanticMemory.from_dir(td)
            skills = [
                TasksPlannerSkill(),
                CodeReviewSkill(),
                DocSummarizerSkill(),
                GitHelperSkill(),
                RememberSkill(semantic),
                RecallSkill(semantic),
            ]
            a = AgentCore(cfg, llm, episodic, semantic, skills)

            out = a.handle_message("/help", user_id="u")
            self.assertIn("/plan", out)
            self.assertIn("/review", out)
            self.assertIn("/doc", out)
            self.assertIn("/git", out)
            self.assertIn("/remember", out)
            self.assertIn("/recall", out)

    def test_non_command_calls_llm(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            cfg = Config(memory_dir=td)
            llm = _FakeLLM()
            episodic = EpisodicMemory.from_dir(td)
            semantic = SemanticMemory.from_dir(td)
            a = AgentCore(cfg, llm, episodic, semantic, [TasksPlannerSkill()])

            out = a.handle_message("hello", user_id="u1")
            self.assertEqual(out, "ok")
            self.assertIsNotNone(llm.last_messages)

