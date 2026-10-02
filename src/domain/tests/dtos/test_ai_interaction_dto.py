from dataclasses import FrozenInstanceError
from unittest import TestCase

from src.domain.dtos.ai_interaction_dto import AiInteractionDTO
from src.domain.dtos.base_dto import BaseDTO
from src.domain.enums.ai_provider import AiProvider
from src.domain.enums.ai_purpose import AiPurpose
from src.domain.enums.execution_status import ExecutionStatus


class TestAiInteractionDTO(TestCase):
    def test_is_subclass_of_base_dto(self):
        self.assertTrue(issubclass(AiInteractionDTO, BaseDTO))

    def test_frozen_raises_on_mutation(self):
        ai_interaction = AiInteractionDTO(
            analysis_id="analysis-123",
            provider=AiProvider.OLLAMA,
            purpose=AiPurpose.ARTICLE_CLASSIFICATION,
            model_name="mistral",
            input_payload="prompt text",
            output_payload="response text",
            duration_ms=320.0,
            status=ExecutionStatus.SUCCESS,
        )
        field_name = "status"
        with self.assertRaises(FrozenInstanceError):
            setattr(ai_interaction, field_name, ExecutionStatus.ERROR)

    def test_holds_expected_attributes(self):
        ai_interaction = AiInteractionDTO(
            analysis_id="analysis-123",
            provider=AiProvider.OLLAMA,
            purpose=AiPurpose.ARTICLE_CLASSIFICATION,
            model_name="mistral",
            input_payload="prompt text",
            output_payload="response text",
            duration_ms=320.0,
            status=ExecutionStatus.SUCCESS,
        )
        self.assertEqual(ai_interaction.analysis_id, "analysis-123")
        self.assertEqual(ai_interaction.provider, AiProvider.OLLAMA)
        self.assertEqual(ai_interaction.purpose, AiPurpose.ARTICLE_CLASSIFICATION)
        self.assertEqual(ai_interaction.model_name, "mistral")
        self.assertEqual(ai_interaction.input_payload, "prompt text")
        self.assertEqual(ai_interaction.output_payload, "response text")
        self.assertEqual(ai_interaction.duration_ms, 320.0)
        self.assertEqual(ai_interaction.status, ExecutionStatus.SUCCESS)
        self.assertIsNone(ai_interaction.prompt_tokens)
        self.assertIsNone(ai_interaction.completion_tokens)
        self.assertIsNone(ai_interaction.done_reason)

    def test_holds_optional_usage_and_done_reason_attributes(self):
        ai_interaction = AiInteractionDTO(
            analysis_id="analysis-456",
            provider=AiProvider.OLLAMA,
            purpose=AiPurpose.QUALITY_ANALYSIS,
            model_name="gemma",
            input_payload="prompt text",
            output_payload="response text",
            duration_ms=450.0,
            status=ExecutionStatus.SUCCESS,
            prompt_tokens=150,
            completion_tokens=75,
            done_reason="length",
        )
        self.assertEqual(ai_interaction.prompt_tokens, 150)
        self.assertEqual(ai_interaction.completion_tokens, 75)
        self.assertEqual(ai_interaction.done_reason, "length")
