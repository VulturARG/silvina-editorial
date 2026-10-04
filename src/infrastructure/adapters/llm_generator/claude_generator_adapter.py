from asyncio import run
from typing import Any

from claude_agent_sdk import (
    AssistantMessage,
    ClaudeAgentOptions,
    ClaudeSDKError,
    RateLimitEvent,
    ResultMessage,
    TextBlock,
    query,
)

from src.domain.dtos.llm_generation_dto import LlmGenerationDTO
from src.domain.enums.llm_done_reason import LlmDoneReason
from src.domain.exceptions.language_model_errors import LanguageModelUnavailable
from src.domain.ports.llm_generator_port import LlmGeneratorPort
from src.infrastructure.adapters.llm_generator.claude_backend_reported_error import (
    ClaudeBackendReportedError,
)

CLAUDE_STOP_REASON_TO_DONE_REASON: dict[str, str] = {
    "end_turn": LlmDoneReason.STOP.value,
    "max_tokens": LlmDoneReason.LENGTH.value,
    "model_context_window_exceeded": LlmDoneReason.LENGTH.value,
}


class ClaudeGeneratorAdapter(LlmGeneratorPort):
    """Generates text via the Claude Agent SDK backend."""

    def __init__(self, model_name: str, think: bool) -> None:
        self._model_name = model_name
        self._think = think

    def generate(self, prompt: str, options: dict | None = None) -> str:
        """Return Claude's generated text for the given prompt."""
        return self.generate_with_usage(prompt=prompt, options=options).text

    def generate_with_usage(self, prompt: str, options: dict | None = None) -> LlmGenerationDTO:
        """Return Claude's generated text and usage metadata for the given prompt."""
        try:
            return run(self._execute_query(prompt=prompt))
        except ClaudeSDKError as exception:
            raise LanguageModelUnavailable() from exception

    def _translate_stop_reason(self, stop_reason: str | None) -> str | None:
        if stop_reason is None:
            return None
        return CLAUDE_STOP_REASON_TO_DONE_REASON.get(stop_reason, stop_reason)

    def _extract_token_count(self, usage: Any, key: str) -> int | None:
        if not isinstance(usage, dict):
            return None
        token_count = usage.get(key)
        if isinstance(token_count, int) and not isinstance(token_count, bool):
            return token_count
        return None

    def _extract_prompt_tokens(self, usage: Any) -> int | None:
        input_tokens = self._extract_token_count(usage=usage, key="input_tokens")
        if input_tokens is None:
            return None
        cache_read_tokens = self._extract_token_count(usage=usage, key="cache_read_input_tokens")
        cache_creation_tokens = self._extract_token_count(
            usage=usage, key="cache_creation_input_tokens"
        )
        return (
            input_tokens
            + (cache_read_tokens if cache_read_tokens is not None else 0)
            + (cache_creation_tokens if cache_creation_tokens is not None else 0)
        )

    def _format_rate_limit_suffix(self, rate_limit_event: RateLimitEvent | None) -> str:
        if rate_limit_event is not None and rate_limit_event.rate_limit_info.status == "rejected":
            rate_limit_info = rate_limit_event.rate_limit_info
            return f"; rate limit rejected (type={rate_limit_info.rate_limit_type}, resets_at={rate_limit_info.resets_at})"
        return ""

    def _build_assistant_error_detail(
        self, message: AssistantMessage, latest_rate_limit_event: RateLimitEvent | None
    ) -> str:
        rate_limit_suffix = self._format_rate_limit_suffix(rate_limit_event=latest_rate_limit_event)
        return f"assistant error: {message.error}{rate_limit_suffix}"

    def _build_result_error_detail(
        self, message: ResultMessage, latest_rate_limit_event: RateLimitEvent | None
    ) -> str:
        rate_limit_suffix = self._format_rate_limit_suffix(rate_limit_event=latest_rate_limit_event)
        return (
            f"result error: subtype={message.subtype}, "
            f"api_error_status={message.api_error_status}, "
            f"errors={message.errors}"
            f"{rate_limit_suffix}"
        )

    async def _execute_query(self, prompt: str) -> LlmGenerationDTO:
        """Execute the asynchronous query against Claude Agent SDK and assemble the result."""
        text_fragments: list[str] = []
        final_result_message: ResultMessage | None = None
        latest_rate_limit_event: RateLimitEvent | None = None

        agent_options_parameters: dict[str, Any] = {
            "model": self._model_name,
            "tools": [],
            "max_turns": 1,
            "setting_sources": [],
            "env": {"ANTHROPIC_API_KEY": "", "ENABLE_CLAUDEAI_MCP_SERVERS": "false"},
        }
        if not self._think:
            agent_options_parameters["thinking"] = {"type": "disabled"}

        agent_options = ClaudeAgentOptions(**agent_options_parameters)

        async for message in query(prompt=prompt, options=agent_options):
            if isinstance(message, RateLimitEvent):
                latest_rate_limit_event = message
            elif isinstance(message, AssistantMessage):
                if message.error is not None:
                    detail = self._build_assistant_error_detail(
                        message=message,
                        latest_rate_limit_event=latest_rate_limit_event,
                    )
                    raise LanguageModelUnavailable() from ClaudeBackendReportedError(detail)
                for block in message.content:
                    if isinstance(block, TextBlock):
                        text_fragments.append(block.text)
            elif isinstance(message, ResultMessage):
                if message.is_error:
                    detail = self._build_result_error_detail(
                        message=message,
                        latest_rate_limit_event=latest_rate_limit_event,
                    )
                    raise LanguageModelUnavailable() from ClaudeBackendReportedError(detail)
                final_result_message = message

        raw_usage = final_result_message.usage if final_result_message is not None else None
        prompt_tokens: int | None = self._extract_prompt_tokens(usage=raw_usage)
        completion_tokens: int | None = self._extract_token_count(
            usage=raw_usage, key="output_tokens"
        )
        stop_reason: str | None = (
            final_result_message.stop_reason if final_result_message is not None else None
        )
        done_reason: str | None = self._translate_stop_reason(stop_reason)

        return LlmGenerationDTO(
            text="".join(text_fragments).strip(),
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            done_reason=done_reason,
        )
