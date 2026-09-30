from dataclasses import FrozenInstanceError
from unittest import TestCase

from src.domain.dtos.ai_interaction_dto import AiInteractionDTO
from src.domain.dtos.base_dto import BaseDTO


class TestAiInteractionDTO(TestCase):
    def test_is_subclass_of_base_dto(self):
        self.assertTrue(issubclass(AiInteractionDTO, BaseDTO))

    def test_frozen_raises_on_mutation(self):
        ai_interaction = AiInteractionDTO(
            analysis_id="analysis-123",
            provider="ollama",
            purpose="classification",
            model_name="mistral",
            input_payload="prompt text",
            output_payload="response text",
            duration_ms=320.0,
            status="success",
        )
        field_name = "status"
        with self.assertRaises(FrozenInstanceError):
            setattr(ai_interaction, field_name, "failed")

    def test_holds_expected_attributes(self):
        ai_interaction = AiInteractionDTO(
            analysis_id="analysis-123",
            provider="ollama",
            purpose="classification",
            model_name="mistral",
            input_payload="prompt text",
            output_payload="response text",
            duration_ms=320.0,
            status="success",
        )
        self.assertEqual(ai_interaction.analysis_id, "analysis-123")
        self.assertEqual(ai_interaction.provider, "ollama")
        self.assertEqual(ai_interaction.purpose, "classification")
        self.assertEqual(ai_interaction.model_name, "mistral")
        self.assertEqual(ai_interaction.input_payload, "prompt text")
        self.assertEqual(ai_interaction.output_payload, "response text")
        self.assertEqual(ai_interaction.duration_ms, 320.0)
        self.assertEqual(ai_interaction.status, "success")
