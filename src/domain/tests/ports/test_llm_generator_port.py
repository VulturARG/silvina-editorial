from unittest import TestCase

from src.domain.dtos.llm_generation_dto import LlmGenerationDTO
from src.domain.ports.llm_generator_port import LlmGeneratorPort


class MinimalLlmGenerator(LlmGeneratorPort):
    def __init__(self, canned_response: str) -> None:
        self._canned_response = canned_response
        self.received_prompt: str | None = None
        self.received_options: dict | None = None

    def generate(self, prompt: str, options: dict | None = None) -> str:
        self.received_prompt = prompt
        self.received_options = options
        return self._canned_response


class TestLlmGeneratorPort(TestCase):
    """Unit tests for the default behavior of LlmGeneratorPort."""

    def test_default_generate_with_usage_returns_dto_with_none_metadata(self):
        generator = MinimalLlmGenerator(canned_response="canned output")
        generation = generator.generate_with_usage(prompt="test prompt")

        self.assertIsInstance(generation, LlmGenerationDTO)
        self.assertEqual(generation.text, "canned output")
        self.assertIsNone(generation.prompt_tokens)
        self.assertIsNone(generation.completion_tokens)
        self.assertIsNone(generation.done_reason)

    def test_default_generate_with_usage_forwards_prompt_and_options(self):
        generator = MinimalLlmGenerator(canned_response="canned output")
        options = {"temperature": 0.5}
        generator.generate_with_usage(prompt="test prompt with options", options=options)

        self.assertEqual(generator.received_prompt, "test prompt with options")
        self.assertEqual(generator.received_options, options)
