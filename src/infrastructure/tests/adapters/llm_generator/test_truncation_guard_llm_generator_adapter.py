from unittest import TestCase

from src.domain.dtos.llm_generation_dto import LlmGenerationDTO
from src.domain.enums.llm_done_reason import LlmDoneReason
from src.domain.exceptions.language_model_errors import LanguageModelOutputTruncated
from src.infrastructure.adapters.llm_generator.truncation_guard_llm_generator_adapter import (
    TruncationGuardLlmGeneratorAdapter,
)
from src.infrastructure.tests.test_doubles.failing_llm_generator_adapter import (
    FailingLlmGeneratorAdapter,
)
from src.infrastructure.tests.test_doubles.fixed_generation_llm_generator_adapter import (
    FixedGenerationLlmGeneratorAdapter,
)


class TestTruncationGuardLlmGeneratorAdapter(TestCase):
    """Unit tests for TruncationGuardLlmGeneratorAdapter."""

    def test_generate_with_usage_raises_output_truncated_when_done_reason_is_length(self) -> None:
        adapter = self._create_adapter(
            generation_result=LlmGenerationDTO(
                text="cut response",
                prompt_tokens=40,
                completion_tokens=128,
                done_reason=LlmDoneReason.LENGTH.value,
            ),
        )

        with self.assertRaises(LanguageModelOutputTruncated):
            adapter.generate_with_usage(prompt="prompt")

    def test_generate_raises_output_truncated_when_done_reason_is_length(self) -> None:
        adapter = self._create_adapter(
            generation_result=LlmGenerationDTO(
                text="cut response",
                prompt_tokens=40,
                completion_tokens=128,
                done_reason=LlmDoneReason.LENGTH.value,
            ),
        )

        with self.assertRaises(LanguageModelOutputTruncated):
            adapter.generate(prompt="prompt")

    def test_generate_with_usage_returns_result_unchanged_when_done_reason_is_stop(self) -> None:
        generation_result = LlmGenerationDTO(
            text="complete response",
            prompt_tokens=40,
            completion_tokens=12,
            done_reason=LlmDoneReason.STOP.value,
        )
        adapter = self._create_adapter(generation_result=generation_result)

        result = adapter.generate_with_usage(prompt="prompt")

        self.assertIs(result, generation_result)

    def test_generate_with_usage_returns_result_unchanged_when_done_reason_is_none(self) -> None:
        generation_result = LlmGenerationDTO(
            text="complete response",
            prompt_tokens=8,
            completion_tokens=5,
            done_reason=None,
        )
        adapter = self._create_adapter(generation_result=generation_result)

        result = adapter.generate_with_usage(prompt="prompt")

        self.assertIs(result, generation_result)

    def test_generate_returns_text_when_done_reason_is_stop(self) -> None:
        adapter = self._create_adapter(
            generation_result=LlmGenerationDTO(
                text="complete response",
                prompt_tokens=40,
                completion_tokens=12,
                done_reason=LlmDoneReason.STOP.value,
            ),
        )

        self.assertEqual(adapter.generate(prompt="prompt"), "complete response")

    def test_generate_with_usage_forwards_prompt_and_options_to_wrapped_generator(self) -> None:
        wrapped_generator = FixedGenerationLlmGeneratorAdapter(
            generation_result=LlmGenerationDTO(
                text="complete response",
                prompt_tokens=40,
                completion_tokens=12,
                done_reason=LlmDoneReason.STOP.value,
            ),
        )
        adapter = TruncationGuardLlmGeneratorAdapter(generator=wrapped_generator)

        adapter.generate_with_usage(prompt="prompt", options={"num_predict": 128})

        self.assertEqual(wrapped_generator.received_prompts, ["prompt"])
        self.assertEqual(wrapped_generator.received_options, [{"num_predict": 128}])

    def test_generate_with_usage_propagates_wrapped_exception_unchanged(self) -> None:
        original_exception = RuntimeError("backend failure")
        adapter = TruncationGuardLlmGeneratorAdapter(
            generator=FailingLlmGeneratorAdapter(exception=original_exception),
        )

        with self.assertRaises(RuntimeError) as error_context:
            adapter.generate_with_usage(prompt="prompt")

        self.assertIs(error_context.exception, original_exception)

    def _create_adapter(
        self,
        generation_result: LlmGenerationDTO,
    ) -> TruncationGuardLlmGeneratorAdapter:
        return TruncationGuardLlmGeneratorAdapter(
            generator=FixedGenerationLlmGeneratorAdapter(generation_result=generation_result),
        )
