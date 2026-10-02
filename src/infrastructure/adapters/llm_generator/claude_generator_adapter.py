from asyncio import run
from typing import Any

from claude_agent_sdk import (
    AssistantMessage,
    ClaudeAgentOptions,
    ClaudeSDKError,
    ResultMessage,
    TextBlock,
    query,
)

from src.domain.dtos.llm_generation_dto import LlmGenerationDTO
from src.domain.exceptions.language_model_errors import LanguageModelUnavailable
from src.domain.ports.llm_generator_port import LlmGeneratorPort


class ClaudeGeneratorAdapter(LlmGeneratorPort):
    """Generates text via the Claude Agent SDK backend."""

    def __init__(self, model_name: str) -> None:
        self._model_name = model_name

    def generate(self, prompt: str, options: dict | None = None) -> str:
        """Return Claude's generated text for the given prompt."""
        return self.generate_with_usage(prompt=prompt, options=options).text

    def generate_with_usage(self, prompt: str, options: dict | None = None) -> LlmGenerationDTO:
        """Return Claude's generated text and usage metadata for the given prompt."""
        try:
            return run(self._execute_query(prompt=prompt))
        except ClaudeSDKError as exception:
            raise LanguageModelUnavailable() from exception

    async def _execute_query(self, prompt: str) -> LlmGenerationDTO:
        """Execute the asynchronous query against Claude Agent SDK and assemble the result."""
        text_fragments: list[str] = []
        final_result_message: ResultMessage | None = None

        agent_options = ClaudeAgentOptions(
            model=self._model_name,
            tools=[],
            max_turns=1,
            setting_sources=[],
            env={"ANTHROPIC_API_KEY": ""},
        )

        async for message in query(prompt=prompt, options=agent_options):
            if isinstance(message, AssistantMessage):
                if message.error is not None:
                    raise LanguageModelUnavailable()
                for block in message.content:
                    if isinstance(block, TextBlock):
                        text_fragments.append(block.text)
            elif isinstance(message, ResultMessage):
                if message.is_error:
                    raise LanguageModelUnavailable()
                final_result_message = message

        usage_dictionary: dict[str, Any] = (
            final_result_message.usage
            if final_result_message is not None and isinstance(final_result_message.usage, dict)
            else {}
        )

        prompt_tokens: int | None = usage_dictionary.get("input_tokens")
        completion_tokens: int | None = usage_dictionary.get("output_tokens")
        done_reason: str | None = (
            final_result_message.stop_reason if final_result_message is not None else None
        )

        return LlmGenerationDTO(
            text="".join(text_fragments).strip(),
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            done_reason=done_reason,
        )
