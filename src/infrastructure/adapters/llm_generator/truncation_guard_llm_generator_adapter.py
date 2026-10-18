from src.domain.dtos.llm_generation_dto import LlmGenerationDTO
from src.domain.enums.llm_done_reason import LlmDoneReason
from src.domain.exceptions.language_model_errors import LanguageModelOutputTruncated
from src.domain.ports.llm_generator_port import LlmGeneratorPort


class TruncationGuardLlmGeneratorAdapter(LlmGeneratorPort):
    """Decorator adapter for LlmGeneratorPort that fails on responses cut by the token limit."""

    def __init__(self, generator: LlmGeneratorPort) -> None:
        self._generator = generator

    def generate(self, prompt: str, options: dict | None = None) -> str:
        """Return the generated text for the given prompt, failing when the response was truncated."""
        return self.generate_with_usage(prompt=prompt, options=options).text

    def generate_with_usage(self, prompt: str, options: dict | None = None) -> LlmGenerationDTO:
        """Return the generated text and usage metadata, failing when the response was truncated."""
        generation_result = self._generator.generate_with_usage(prompt=prompt, options=options)
        if generation_result.done_reason == LlmDoneReason.LENGTH.value:
            raise LanguageModelOutputTruncated()
        return generation_result
