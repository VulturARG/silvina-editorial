from src.domain.dtos.llm_generation_dto import LlmGenerationDTO
from src.domain.ports.llm_generator_port import LlmGeneratorPort


class FixedGenerationLlmGeneratorAdapter(LlmGeneratorPort):
    """Test double for LlmGeneratorPort that returns a preconfigured generation."""

    def __init__(self, generation_result: LlmGenerationDTO) -> None:
        self._generation_result = generation_result
        self.received_prompts: list[str] = []
        self.received_options: list[dict | None] = []

    def generate(self, prompt: str, options: dict | None = None) -> str:
        """Return the preconfigured generated text."""
        return self.generate_with_usage(prompt=prompt, options=options).text

    def generate_with_usage(self, prompt: str, options: dict | None = None) -> LlmGenerationDTO:
        """Return the preconfigured generation and record the received prompt and options."""
        self.received_prompts.append(prompt)
        self.received_options.append(options)
        return self._generation_result
