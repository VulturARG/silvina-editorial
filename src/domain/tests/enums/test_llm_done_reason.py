from unittest import TestCase

from src.domain.enums.llm_done_reason import LlmDoneReason


class TestLlmDoneReason(TestCase):
    def test_members_and_values(self):
        self.assertEqual(LlmDoneReason.STOP.value, "stop")
        self.assertEqual(LlmDoneReason.LENGTH.value, "length")

    def test_lookup_by_value(self):
        self.assertIs(LlmDoneReason("stop"), LlmDoneReason.STOP)
        self.assertIs(LlmDoneReason("length"), LlmDoneReason.LENGTH)

    def test_is_subclass_of_str_and_enum(self):
        self.assertTrue(issubclass(LlmDoneReason, str))
        self.assertEqual(LlmDoneReason.STOP, "stop")
        self.assertEqual(LlmDoneReason.LENGTH, "length")

    def test_invalid_value_raises_value_error(self):
        with self.assertRaises(ValueError):
            LlmDoneReason("invalid")

    def test_member_count(self):
        self.assertEqual(len(LlmDoneReason), 2)
