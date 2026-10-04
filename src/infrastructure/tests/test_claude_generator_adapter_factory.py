from unittest import TestCase

from src.domain.ports.llm_generator_port import LlmGeneratorPort
from src.infrastructure.adapters.llm_generator.claude_generator_adapter import (
    ClaudeGeneratorAdapter,
)
from src.infrastructure.adapters.llm_generator.claude_message_digest_builder import (
    ClaudeMessageDigestBuilder,
)
from src.infrastructure.wirings.claude_generator_adapter_factory import (
    ClaudeGeneratorAdapterFactory,
)


class TestClaudeGeneratorAdapterFactory(TestCase):
    def test_create_returns_claude_generator_adapter_as_llm_generator_port(self):
        generator = ClaudeGeneratorAdapterFactory().create(
            model_name="claude-haiku-4-5-20251001", think=False
        )

        self.assertIsInstance(generator, LlmGeneratorPort)
        self.assertIsInstance(generator, ClaudeGeneratorAdapter)

    def test_create_forwards_model_name_and_think_flag(self):
        generator = ClaudeGeneratorAdapterFactory().create(model_name="custom-model", think=True)

        assert isinstance(generator, ClaudeGeneratorAdapter)
        self.assertEqual(generator._model_name, "custom-model")
        self.assertTrue(generator._think)

    def test_create_injects_a_message_digest_builder(self):
        generator = ClaudeGeneratorAdapterFactory().create(
            model_name="claude-haiku-4-5-20251001", think=False
        )

        assert isinstance(generator, ClaudeGeneratorAdapter)
        self.assertIsInstance(generator._message_digest_builder, ClaudeMessageDigestBuilder)
