from unittest import TestCase

from src.domain.enums.ai_provider import AiProvider


class TestAiProvider(TestCase):
    def test_members_and_values(self):
        self.assertEqual(AiProvider.OLLAMA.value, "ollama")
        self.assertEqual(AiProvider.CLAUDE.value, "claude")

    def test_lookup_by_value(self):
        self.assertIs(AiProvider("ollama"), AiProvider.OLLAMA)
        self.assertIs(AiProvider("claude"), AiProvider.CLAUDE)

    def test_invalid_value_raises_value_error(self):
        with self.assertRaises(ValueError):
            AiProvider("invalid")

    def test_member_count(self):
        self.assertEqual(len(AiProvider), 2)

    def test_importable_independently(self):
        self.assertIsNotNone(AiProvider)
