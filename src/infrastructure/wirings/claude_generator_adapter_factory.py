from src.domain.ports.llm_generator_port import LlmGeneratorPort
from src.infrastructure.adapters.llm_generator.claude_generator_adapter import (
    ClaudeGeneratorAdapter,
)
from src.infrastructure.adapters.llm_generator.claude_message_digest_builder import (
    ClaudeMessageDigestBuilder,
)


class ClaudeGeneratorAdapterFactory:
    """Assembles the Claude generator adapter with its collaborators."""

    def create(self, model_name: str, think: bool) -> LlmGeneratorPort:
        """Return a Claude generator adapter for the given model and reasoning flag."""
        return ClaudeGeneratorAdapter(
            model_name=model_name,
            think=think,
            message_digest_builder=ClaudeMessageDigestBuilder(),
        )
