from dataclasses import FrozenInstanceError
from unittest import TestCase

from src.domain.dtos.base_dto import BaseDTO
from src.domain.dtos.llm_generation_dto import LlmGenerationDTO


class TestLlmGenerationDTO(TestCase):
    def test_is_subclass_of_base_dto(self):
        self.assertTrue(issubclass(LlmGenerationDTO, BaseDTO))

    def test_holds_expected_attributes_with_usage(self):
        generation = LlmGenerationDTO(
            text="generated content",
            prompt_tokens=42,
            completion_tokens=18,
            done_reason="stop",
        )
        self.assertEqual(generation.text, "generated content")
        self.assertEqual(generation.prompt_tokens, 42)
        self.assertEqual(generation.completion_tokens, 18)
        self.assertEqual(generation.done_reason, "stop")

    def test_holds_none_metadata_attributes(self):
        generation = LlmGenerationDTO(
            text="generated content without tokens",
            prompt_tokens=None,
            completion_tokens=None,
            done_reason=None,
        )
        self.assertEqual(generation.text, "generated content without tokens")
        self.assertIsNone(generation.prompt_tokens)
        self.assertIsNone(generation.completion_tokens)
        self.assertIsNone(generation.done_reason)

    def test_frozen_raises_on_mutation(self):
        generation = LlmGenerationDTO(
            text="initial text",
            prompt_tokens=10,
            completion_tokens=5,
            done_reason="stop",
        )
        field_name = "text"
        with self.assertRaises(FrozenInstanceError):
            setattr(generation, field_name, "mutated text")

    def test_round_trip_dictionary_serialization(self):
        generation = LlmGenerationDTO(
            text="serialized content",
            prompt_tokens=100,
            completion_tokens=50,
            done_reason="length",
        )
        data = generation.as_dict()
        restored = LlmGenerationDTO.from_dict(data)
        self.assertEqual(generation, restored)
