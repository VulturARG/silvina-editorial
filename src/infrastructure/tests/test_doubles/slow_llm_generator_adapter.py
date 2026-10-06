from time import sleep

from src.domain.ports.llm_generator_port import LlmGeneratorPort


class SlowLlmGeneratorAdapter(LlmGeneratorPort):
    """Test double for LlmGeneratorPort that introduces a delay before returning."""

    def __init__(self, response: str, delay_seconds: float) -> None:
        self._response = response
        self._delay_seconds = delay_seconds

    def generate(self, prompt: str, options: dict | None = None) -> str:
        """Sleep for the configured delay duration and return the preset response."""
        sleep(self._delay_seconds)
        return self._response
