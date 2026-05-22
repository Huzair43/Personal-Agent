import unittest

from agent.llm.base import LLMMessage, LLMRole


class TestLLMBase(unittest.TestCase):
    def test_roles_values(self) -> None:
        self.assertEqual(LLMRole.SYSTEM.value, "system")
        self.assertEqual(LLMRole.USER.value, "user")
        self.assertEqual(LLMRole.ASSISTANT.value, "assistant")

    def test_message(self) -> None:
        m = LLMMessage(role=LLMRole.USER, content="hi")
        self.assertEqual(m.role, LLMRole.USER)
        self.assertEqual(m.content, "hi")

