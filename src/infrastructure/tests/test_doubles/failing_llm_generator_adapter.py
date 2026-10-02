from src.domain.ports.llm_generator_port import LlmGeneratorPort


class FailingLlmGeneratorAdapter(LlmGeneratorPort):
    """Test double for LlmGeneratorPort that raises a preconfigured exception on generation."""

    def __init__(self, exception: Exception) -> None:
        self._exception = exception

    def generate(self, prompt: str, options: dict | None = None) -> str:
        """Raise the preconfigured exception."""
        raise self._exception
