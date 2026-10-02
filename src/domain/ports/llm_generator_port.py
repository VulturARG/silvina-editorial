from abc import ABC, abstractmethod

from src.domain.dtos.llm_generation_dto import LlmGenerationDTO


class LlmGeneratorPort(ABC):
    """Capability to generate text from a prompt via a language model backend."""

    @abstractmethod
    def generate(self, prompt: str, options: dict | None = None) -> str:
        """Return the generated text for the given prompt."""

    def generate_with_usage(self, prompt: str, options: dict | None = None) -> LlmGenerationDTO:
        """Return the text with the usage metadata when the backend reports it."""
        return LlmGenerationDTO(
            text=self.generate(prompt=prompt, options=options),
            prompt_tokens=None,
            completion_tokens=None,
            done_reason=None,
        )
