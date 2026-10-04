from collections.abc import AsyncIterator
from typing import Any, cast
from unittest import TestCase
from unittest.mock import MagicMock, patch

from claude_agent_sdk import (
    AssistantMessage,
    CLIConnectionError,
    CLINotFoundError,
    ClaudeAgentOptions,
    ClaudeSDKError,
    ProcessError,
    RateLimitEvent,
    RateLimitInfo,
    ResultMessage,
    TextBlock,
    ThinkingBlock,
)

from src.domain.dtos.llm_generation_dto import LlmGenerationDTO
from src.domain.enums.llm_done_reason import LlmDoneReason
from src.domain.exceptions.language_model_errors import LanguageModelUnavailable
from src.infrastructure.adapters.llm_generator.claude_backend_reported_error import (
    ClaudeBackendReportedError,
)
from src.infrastructure.adapters.llm_generator.claude_generator_adapter import (
    ClaudeGeneratorAdapter,
)


class TestClaudeGeneratorAdapter(TestCase):
    """Unit tests for the ClaudeGeneratorAdapter class."""

    def setUp(self) -> None:
        self.model_name = "claude-sonnet-4-5-20250929"
        self.sample_prompt = "Analyze this text"
        self.sample_options = {"temperature": 0.2, "num_predict": 500}
        self.adapter = ClaudeGeneratorAdapter(
            model_name=self.model_name,
            think=False,
        )

    def _create_fake_query(
        self,
        messages_to_yield: list[Any],
    ) -> Any:
        async def fake_query(*args: Any, **kwargs: Any) -> AsyncIterator[Any]:
            for message in messages_to_yield:
                yield message

        return fake_query

    def _create_failing_query(
        self,
        exception_to_raise: Exception,
    ) -> Any:
        async def fake_query(*args: Any, **kwargs: Any) -> AsyncIterator[Any]:
            raise exception_to_raise
            yield

        return fake_query

    @patch("src.infrastructure.adapters.llm_generator.claude_generator_adapter.query")
    def test_generate_returns_stripped_response_text(self, mock_query: MagicMock) -> None:
        mock_query.side_effect = self._create_fake_query(
            [
                AssistantMessage(
                    content=[TextBlock(text="  analyzed response text  ")],
                    model=self.model_name,
                ),
            ]
        )

        result = self.adapter.generate(prompt=self.sample_prompt)

        self.assertEqual(result, "analyzed response text")

    @patch("src.infrastructure.adapters.llm_generator.claude_generator_adapter.query")
    def test_generate_returns_empty_string_when_content_is_empty(
        self, mock_query: MagicMock
    ) -> None:
        mock_query.side_effect = self._create_fake_query(
            [
                AssistantMessage(
                    content=[],
                    model=self.model_name,
                ),
            ]
        )

        result = self.adapter.generate(prompt=self.sample_prompt)

        self.assertEqual(result, "")

    @patch("src.infrastructure.adapters.llm_generator.claude_generator_adapter.query")
    def test_generate_concatenates_multiple_text_blocks_across_assistant_messages(
        self, mock_query: MagicMock
    ) -> None:
        mock_query.side_effect = self._create_fake_query(
            [
                AssistantMessage(
                    content=[
                        TextBlock(text="Hello, "),
                        TextBlock(text="world! "),
                    ],
                    model=self.model_name,
                ),
                AssistantMessage(
                    content=[
                        TextBlock(text="How are you?"),
                    ],
                    model=self.model_name,
                ),
            ]
        )

        result = self.adapter.generate(prompt=self.sample_prompt)

        self.assertEqual(result, "Hello, world! How are you?")

    @patch("src.infrastructure.adapters.llm_generator.claude_generator_adapter.query")
    def test_generate_ignores_non_text_content_blocks(self, mock_query: MagicMock) -> None:
        mock_query.side_effect = self._create_fake_query(
            [
                AssistantMessage(
                    content=[
                        ThinkingBlock(thinking="internal thoughts", signature="signature-token"),
                        TextBlock(text="final answer"),
                    ],
                    model=self.model_name,
                ),
            ]
        )

        result = self.adapter.generate(prompt=self.sample_prompt)

        self.assertEqual(result, "final answer")

    @patch("src.infrastructure.adapters.llm_generator.claude_generator_adapter.query")
    def test_generate_with_usage_returns_dto_with_text_and_usage_metadata(
        self, mock_query: MagicMock
    ) -> None:
        mock_query.side_effect = self._create_fake_query(
            [
                AssistantMessage(
                    content=[TextBlock(text="  analyzed content  ")],
                    model=self.model_name,
                ),
                ResultMessage(
                    subtype="success",
                    duration_ms=200,
                    duration_api_ms=180,
                    is_error=False,
                    num_turns=1,
                    session_id="test-session-identifier",
                    stop_reason="end_turn",
                    usage={"input_tokens": 128, "output_tokens": 64},
                ),
            ]
        )

        result = self.adapter.generate_with_usage(prompt=self.sample_prompt)

        self.assertIsInstance(result, LlmGenerationDTO)
        self.assertEqual(result.text, "analyzed content")
        self.assertEqual(result.prompt_tokens, 128)
        self.assertEqual(result.completion_tokens, 64)
        self.assertEqual(result.done_reason, LlmDoneReason.STOP.value)

    @patch("src.infrastructure.adapters.llm_generator.claude_generator_adapter.query")
    def test_generate_with_usage_returns_none_metadata_when_usage_missing(
        self, mock_query: MagicMock
    ) -> None:
        mock_query.side_effect = self._create_fake_query(
            [
                AssistantMessage(
                    content=[TextBlock(text="simple response")],
                    model=self.model_name,
                ),
                ResultMessage(
                    subtype="success",
                    duration_ms=100,
                    duration_api_ms=90,
                    is_error=False,
                    num_turns=1,
                    session_id="test-session-identifier",
                    stop_reason=None,
                    usage=None,
                ),
            ]
        )

        result = self.adapter.generate_with_usage(prompt=self.sample_prompt)

        self.assertIsInstance(result, LlmGenerationDTO)
        self.assertEqual(result.text, "simple response")
        self.assertIsNone(result.prompt_tokens)
        self.assertIsNone(result.completion_tokens)
        self.assertIsNone(result.done_reason)

    @patch("src.infrastructure.adapters.llm_generator.claude_generator_adapter.query")
    def test_generate_with_usage_maps_end_turn_stop_reason_to_stop_done_reason(
        self, mock_query: MagicMock
    ) -> None:
        mock_query.side_effect = self._create_fake_query(
            [
                ResultMessage(
                    subtype="success",
                    duration_ms=100,
                    duration_api_ms=90,
                    is_error=False,
                    num_turns=1,
                    session_id="test-session-identifier",
                    stop_reason="end_turn",
                ),
            ]
        )

        result = self.adapter.generate_with_usage(prompt=self.sample_prompt)

        self.assertEqual(result.done_reason, LlmDoneReason.STOP.value)

    @patch("src.infrastructure.adapters.llm_generator.claude_generator_adapter.query")
    def test_generate_with_usage_maps_max_tokens_stop_reason_to_length_done_reason(
        self, mock_query: MagicMock
    ) -> None:
        mock_query.side_effect = self._create_fake_query(
            [
                ResultMessage(
                    subtype="success",
                    duration_ms=100,
                    duration_api_ms=90,
                    is_error=False,
                    num_turns=1,
                    session_id="test-session-identifier",
                    stop_reason="max_tokens",
                ),
            ]
        )

        result = self.adapter.generate_with_usage(prompt=self.sample_prompt)

        self.assertEqual(result.done_reason, LlmDoneReason.LENGTH.value)

    @patch("src.infrastructure.adapters.llm_generator.claude_generator_adapter.query")
    def test_generate_with_usage_maps_model_context_window_exceeded_to_length_done_reason(
        self, mock_query: MagicMock
    ) -> None:
        mock_query.side_effect = self._create_fake_query(
            [
                ResultMessage(
                    subtype="success",
                    duration_ms=100,
                    duration_api_ms=90,
                    is_error=False,
                    num_turns=1,
                    session_id="test-session-identifier",
                    stop_reason="model_context_window_exceeded",
                ),
            ]
        )

        result = self.adapter.generate_with_usage(prompt=self.sample_prompt)

        self.assertEqual(result.done_reason, LlmDoneReason.LENGTH.value)

    @patch("src.infrastructure.adapters.llm_generator.claude_generator_adapter.query")
    def test_generate_with_usage_preserves_unmapped_stop_reason_verbatim(
        self, mock_query: MagicMock
    ) -> None:
        mock_query.side_effect = self._create_fake_query(
            [
                ResultMessage(
                    subtype="success",
                    duration_ms=100,
                    duration_api_ms=90,
                    is_error=False,
                    num_turns=1,
                    session_id="test-session-identifier",
                    stop_reason="refusal",
                ),
            ]
        )

        result = self.adapter.generate_with_usage(prompt=self.sample_prompt)

        self.assertEqual(result.done_reason, "refusal")

    @patch("src.infrastructure.adapters.llm_generator.claude_generator_adapter.query")
    def test_generate_with_usage_preserves_none_stop_reason(self, mock_query: MagicMock) -> None:
        mock_query.side_effect = self._create_fake_query(
            [
                ResultMessage(
                    subtype="success",
                    duration_ms=100,
                    duration_api_ms=90,
                    is_error=False,
                    num_turns=1,
                    session_id="test-session-identifier",
                    stop_reason=None,
                ),
            ]
        )

        result = self.adapter.generate_with_usage(prompt=self.sample_prompt)

        self.assertIsNone(result.done_reason)

    @patch("src.infrastructure.adapters.llm_generator.claude_generator_adapter.query")
    def test_generate_with_usage_returns_none_tokens_when_keys_missing_in_usage_dict(
        self, mock_query: MagicMock
    ) -> None:
        mock_query.side_effect = self._create_fake_query(
            [
                AssistantMessage(
                    content=[TextBlock(text="simple response")],
                    model=self.model_name,
                ),
                ResultMessage(
                    subtype="success",
                    duration_ms=100,
                    duration_api_ms=90,
                    is_error=False,
                    num_turns=1,
                    session_id="test-session-identifier",
                    stop_reason="stop",
                    usage={},
                ),
            ]
        )

        result = self.adapter.generate_with_usage(prompt=self.sample_prompt)

        self.assertIsInstance(result, LlmGenerationDTO)
        self.assertEqual(result.text, "simple response")
        self.assertIsNone(result.prompt_tokens)
        self.assertIsNone(result.completion_tokens)
        self.assertEqual(result.done_reason, "stop")

    @patch("src.infrastructure.adapters.llm_generator.claude_generator_adapter.query")
    def test_generate_with_usage_returns_none_metadata_when_no_result_message_yielded(
        self, mock_query: MagicMock
    ) -> None:
        mock_query.side_effect = self._create_fake_query(
            [
                AssistantMessage(
                    content=[TextBlock(text="simple response")],
                    model=self.model_name,
                ),
            ]
        )

        result = self.adapter.generate_with_usage(prompt=self.sample_prompt)

        self.assertIsInstance(result, LlmGenerationDTO)
        self.assertEqual(result.text, "simple response")
        self.assertIsNone(result.prompt_tokens)
        self.assertIsNone(result.completion_tokens)
        self.assertIsNone(result.done_reason)

    @patch("src.infrastructure.adapters.llm_generator.claude_generator_adapter.query")
    def test_generate_ignores_domain_options_silently(self, mock_query: MagicMock) -> None:
        mock_query.side_effect = self._create_fake_query(
            [
                AssistantMessage(
                    content=[TextBlock(text="answer")],
                    model=self.model_name,
                ),
            ]
        )

        self.adapter.generate(prompt=self.sample_prompt, options=self.sample_options)

        expected_options = ClaudeAgentOptions(
            model=self.model_name,
            tools=[],
            max_turns=1,
            setting_sources=[],
            env={"ANTHROPIC_API_KEY": "", "ENABLE_CLAUDEAI_MCP_SERVERS": "false"},
            thinking={"type": "disabled"},
        )
        mock_query.assert_called_once_with(
            prompt=self.sample_prompt,
            options=expected_options,
        )

    @patch("src.infrastructure.adapters.llm_generator.claude_generator_adapter.query")
    def test_generate_with_usage_ignores_domain_options_silently(
        self, mock_query: MagicMock
    ) -> None:
        mock_query.side_effect = self._create_fake_query(
            [
                AssistantMessage(
                    content=[TextBlock(text="answer")],
                    model=self.model_name,
                ),
            ]
        )

        self.adapter.generate_with_usage(prompt=self.sample_prompt, options=self.sample_options)

        expected_options = ClaudeAgentOptions(
            model=self.model_name,
            tools=[],
            max_turns=1,
            setting_sources=[],
            env={"ANTHROPIC_API_KEY": "", "ENABLE_CLAUDEAI_MCP_SERVERS": "false"},
            thinking={"type": "disabled"},
        )
        mock_query.assert_called_once_with(
            prompt=self.sample_prompt,
            options=expected_options,
        )

    @patch("src.infrastructure.adapters.llm_generator.claude_generator_adapter.query")
    def test_generate_passes_exact_claude_agent_options(self, mock_query: MagicMock) -> None:
        mock_query.side_effect = self._create_fake_query(
            [
                AssistantMessage(
                    content=[TextBlock(text="answer")],
                    model=self.model_name,
                ),
            ]
        )

        self.adapter.generate(prompt=self.sample_prompt)

        expected_options = ClaudeAgentOptions(
            model=self.model_name,
            tools=[],
            max_turns=1,
            setting_sources=[],
            env={"ANTHROPIC_API_KEY": "", "ENABLE_CLAUDEAI_MCP_SERVERS": "false"},
            thinking={"type": "disabled"},
        )
        mock_query.assert_called_once_with(
            prompt=self.sample_prompt,
            options=expected_options,
        )

    @patch("src.infrastructure.adapters.llm_generator.claude_generator_adapter.query")
    def test_generate_passes_claude_agent_options_with_thinking_disabled_when_think_is_false(
        self, mock_query: MagicMock
    ) -> None:
        mock_query.side_effect = self._create_fake_query(
            [
                AssistantMessage(
                    content=[TextBlock(text="answer")],
                    model=self.model_name,
                ),
            ]
        )
        adapter = ClaudeGeneratorAdapter(
            model_name=self.model_name,
            think=False,
        )

        adapter.generate(prompt=self.sample_prompt)

        expected_options = ClaudeAgentOptions(
            model=self.model_name,
            tools=[],
            max_turns=1,
            setting_sources=[],
            env={"ANTHROPIC_API_KEY": "", "ENABLE_CLAUDEAI_MCP_SERVERS": "false"},
            thinking={"type": "disabled"},
        )
        mock_query.assert_called_once_with(
            prompt=self.sample_prompt,
            options=expected_options,
        )

    @patch("src.infrastructure.adapters.llm_generator.claude_generator_adapter.query")
    def test_generate_passes_claude_agent_options_without_thinking_when_think_is_true(
        self, mock_query: MagicMock
    ) -> None:
        mock_query.side_effect = self._create_fake_query(
            [
                AssistantMessage(
                    content=[TextBlock(text="answer")],
                    model=self.model_name,
                ),
            ]
        )
        adapter = ClaudeGeneratorAdapter(
            model_name=self.model_name,
            think=True,
        )

        adapter.generate(prompt=self.sample_prompt)

        expected_options = ClaudeAgentOptions(
            model=self.model_name,
            tools=[],
            max_turns=1,
            setting_sources=[],
            env={"ANTHROPIC_API_KEY": "", "ENABLE_CLAUDEAI_MCP_SERVERS": "false"},
        )
        mock_query.assert_called_once_with(
            prompt=self.sample_prompt,
            options=expected_options,
        )

    @patch("src.infrastructure.adapters.llm_generator.claude_generator_adapter.query")
    def test_generate_raises_language_model_unavailable_on_claude_sdk_error(
        self, mock_query: MagicMock
    ) -> None:
        backend_error = ClaudeSDKError("backend failure")
        mock_query.side_effect = self._create_failing_query(backend_error)

        with self.assertRaises(LanguageModelUnavailable) as context:
            self.adapter.generate(prompt=self.sample_prompt)

        self.assertIs(context.exception.__cause__, backend_error)

    @patch("src.infrastructure.adapters.llm_generator.claude_generator_adapter.query")
    def test_generate_raises_language_model_unavailable_on_cli_not_found_error(
        self, mock_query: MagicMock
    ) -> None:
        backend_error = CLINotFoundError("Claude Code not found")
        mock_query.side_effect = self._create_failing_query(backend_error)

        with self.assertRaises(LanguageModelUnavailable) as context:
            self.adapter.generate(prompt=self.sample_prompt)

        self.assertIs(context.exception.__cause__, backend_error)

    @patch("src.infrastructure.adapters.llm_generator.claude_generator_adapter.query")
    def test_generate_raises_language_model_unavailable_on_cli_connection_error(
        self, mock_query: MagicMock
    ) -> None:
        backend_error = CLIConnectionError("Unable to connect to Claude Code")
        mock_query.side_effect = self._create_failing_query(backend_error)

        with self.assertRaises(LanguageModelUnavailable) as context:
            self.adapter.generate(prompt=self.sample_prompt)

        self.assertIs(context.exception.__cause__, backend_error)

    @patch("src.infrastructure.adapters.llm_generator.claude_generator_adapter.query")
    def test_generate_raises_language_model_unavailable_on_process_error(
        self, mock_query: MagicMock
    ) -> None:
        backend_error = ProcessError("Process failed", exit_code=1)
        mock_query.side_effect = self._create_failing_query(backend_error)

        with self.assertRaises(LanguageModelUnavailable) as context:
            self.adapter.generate(prompt=self.sample_prompt)

        self.assertIs(context.exception.__cause__, backend_error)

    @patch("src.infrastructure.adapters.llm_generator.claude_generator_adapter.query")
    def test_generate_raises_language_model_unavailable_on_assistant_message_error(
        self, mock_query: MagicMock
    ) -> None:
        mock_query.side_effect = self._create_fake_query(
            [
                AssistantMessage(
                    content=[TextBlock(text="API error")],
                    model=self.model_name,
                    error="rate_limit",
                ),
            ]
        )

        with self.assertRaises(LanguageModelUnavailable) as context:
            self.adapter.generate(prompt=self.sample_prompt)

        self.assertIsInstance(context.exception.__cause__, ClaudeBackendReportedError)
        self.assertEqual(str(context.exception.__cause__), "assistant error: rate_limit")

    @patch("src.infrastructure.adapters.llm_generator.claude_generator_adapter.query")
    def test_generate_raises_language_model_unavailable_on_result_message_error(
        self, mock_query: MagicMock
    ) -> None:
        mock_query.side_effect = self._create_fake_query(
            [
                ResultMessage(
                    subtype="error_during_execution",
                    duration_ms=50,
                    duration_api_ms=50,
                    is_error=True,
                    num_turns=1,
                    session_id="test-session-identifier",
                ),
            ]
        )

        with self.assertRaises(LanguageModelUnavailable) as context:
            self.adapter.generate(prompt=self.sample_prompt)

        self.assertIsInstance(context.exception.__cause__, ClaudeBackendReportedError)
        self.assertEqual(
            str(context.exception.__cause__),
            "result error: subtype=error_during_execution, api_error_status=None, errors=None",
        )

    @patch("src.infrastructure.adapters.llm_generator.claude_generator_adapter.query")
    def test_generate_includes_all_fields_in_result_error_cause(
        self, mock_query: MagicMock
    ) -> None:
        mock_query.side_effect = self._create_fake_query(
            [
                ResultMessage(
                    subtype="api_error",
                    duration_ms=50,
                    duration_api_ms=50,
                    is_error=True,
                    num_turns=1,
                    session_id="test-session-identifier",
                    api_error_status=429,
                    errors=["rate limit exceeded"],
                ),
            ]
        )

        with self.assertRaises(LanguageModelUnavailable) as context:
            self.adapter.generate(prompt=self.sample_prompt)

        self.assertIsInstance(context.exception.__cause__, ClaudeBackendReportedError)
        self.assertEqual(
            str(context.exception.__cause__),
            "result error: subtype=api_error, api_error_status=429, errors=['rate limit exceeded']",
        )

    @patch("src.infrastructure.adapters.llm_generator.claude_generator_adapter.query")
    def test_generate_appends_rate_limit_rejected_suffix_to_assistant_error_when_status_is_rejected(
        self, mock_query: MagicMock
    ) -> None:
        mock_query.side_effect = self._create_fake_query(
            [
                RateLimitEvent(
                    rate_limit_info=RateLimitInfo(
                        status="rejected",
                        rate_limit_type="five_hour",
                        resets_at=1735689600,
                    ),
                    uuid="rate-limit-uuid",
                    session_id="test-session-identifier",
                ),
                AssistantMessage(
                    content=[TextBlock(text="API error")],
                    model=self.model_name,
                    error="rate_limit",
                ),
            ]
        )

        with self.assertRaises(LanguageModelUnavailable) as context:
            self.adapter.generate(prompt=self.sample_prompt)

        self.assertIsInstance(context.exception.__cause__, ClaudeBackendReportedError)
        self.assertEqual(
            str(context.exception.__cause__),
            "assistant error: rate_limit; rate limit rejected (type=five_hour, resets_at=1735689600)",
        )

    @patch("src.infrastructure.adapters.llm_generator.claude_generator_adapter.query")
    def test_generate_appends_rate_limit_rejected_suffix_to_result_error_when_status_is_rejected(
        self, mock_query: MagicMock
    ) -> None:
        mock_query.side_effect = self._create_fake_query(
            [
                RateLimitEvent(
                    rate_limit_info=RateLimitInfo(
                        status="rejected",
                        rate_limit_type="seven_day",
                        resets_at=1735690000,
                    ),
                    uuid="rate-limit-uuid",
                    session_id="test-session-identifier",
                ),
                ResultMessage(
                    subtype="error_during_execution",
                    duration_ms=50,
                    duration_api_ms=50,
                    is_error=True,
                    num_turns=1,
                    session_id="test-session-identifier",
                    api_error_status=529,
                    errors=["overloaded"],
                ),
            ]
        )

        with self.assertRaises(LanguageModelUnavailable) as context:
            self.adapter.generate(prompt=self.sample_prompt)

        self.assertIsInstance(context.exception.__cause__, ClaudeBackendReportedError)
        self.assertEqual(
            str(context.exception.__cause__),
            "result error: subtype=error_during_execution, api_error_status=529, errors=['overloaded']; rate limit rejected (type=seven_day, resets_at=1735690000)",
        )

    @patch("src.infrastructure.adapters.llm_generator.claude_generator_adapter.query")
    def test_generate_omits_rate_limit_suffix_when_status_is_allowed(
        self, mock_query: MagicMock
    ) -> None:
        mock_query.side_effect = self._create_fake_query(
            [
                RateLimitEvent(
                    rate_limit_info=RateLimitInfo(
                        status="allowed",
                        rate_limit_type="five_hour",
                        resets_at=1735689600,
                    ),
                    uuid="rate-limit-uuid",
                    session_id="test-session-identifier",
                ),
                AssistantMessage(
                    content=[TextBlock(text="API error")],
                    model=self.model_name,
                    error="server_error",
                ),
            ]
        )

        with self.assertRaises(LanguageModelUnavailable) as context:
            self.adapter.generate(prompt=self.sample_prompt)

        self.assertIsInstance(context.exception.__cause__, ClaudeBackendReportedError)
        self.assertEqual(str(context.exception.__cause__), "assistant error: server_error")

    @patch("src.infrastructure.adapters.llm_generator.claude_generator_adapter.query")
    def test_generate_omits_rate_limit_suffix_when_status_is_allowed_warning(
        self, mock_query: MagicMock
    ) -> None:
        mock_query.side_effect = self._create_fake_query(
            [
                RateLimitEvent(
                    rate_limit_info=RateLimitInfo(
                        status="allowed_warning",
                        rate_limit_type="five_hour",
                        resets_at=1735689600,
                    ),
                    uuid="rate-limit-uuid",
                    session_id="test-session-identifier",
                ),
                AssistantMessage(
                    content=[TextBlock(text="API error")],
                    model=self.model_name,
                    error="server_error",
                ),
            ]
        )

        with self.assertRaises(LanguageModelUnavailable) as context:
            self.adapter.generate(prompt=self.sample_prompt)

        self.assertIsInstance(context.exception.__cause__, ClaudeBackendReportedError)
        self.assertEqual(str(context.exception.__cause__), "assistant error: server_error")

    @patch("src.infrastructure.adapters.llm_generator.claude_generator_adapter.query")
    def test_generate_omits_rate_limit_suffix_when_no_rate_limit_event_seen(
        self, mock_query: MagicMock
    ) -> None:
        mock_query.side_effect = self._create_fake_query(
            [
                AssistantMessage(
                    content=[TextBlock(text="API error")],
                    model=self.model_name,
                    error="authentication_failed",
                ),
            ]
        )

        with self.assertRaises(LanguageModelUnavailable) as context:
            self.adapter.generate(prompt=self.sample_prompt)

        self.assertIsInstance(context.exception.__cause__, ClaudeBackendReportedError)
        self.assertEqual(str(context.exception.__cause__), "assistant error: authentication_failed")

    @patch("src.infrastructure.adapters.llm_generator.claude_generator_adapter.query")
    def test_generate_tracks_latest_rate_limit_event_in_stream(self, mock_query: MagicMock) -> None:
        mock_query.side_effect = self._create_fake_query(
            [
                RateLimitEvent(
                    rate_limit_info=RateLimitInfo(
                        status="rejected",
                        rate_limit_type="five_hour",
                        resets_at=1735689600,
                    ),
                    uuid="rate-limit-uuid-1",
                    session_id="test-session-identifier",
                ),
                RateLimitEvent(
                    rate_limit_info=RateLimitInfo(
                        status="allowed",
                        rate_limit_type="five_hour",
                        resets_at=1735689600,
                    ),
                    uuid="rate-limit-uuid-2",
                    session_id="test-session-identifier",
                ),
                AssistantMessage(
                    content=[TextBlock(text="API error")],
                    model=self.model_name,
                    error="unknown",
                ),
            ]
        )

        with self.assertRaises(LanguageModelUnavailable) as context:
            self.adapter.generate(prompt=self.sample_prompt)

        self.assertIsInstance(context.exception.__cause__, ClaudeBackendReportedError)
        self.assertEqual(str(context.exception.__cause__), "assistant error: unknown")

    @patch("src.infrastructure.adapters.llm_generator.claude_generator_adapter.query")
    def test_generate_detail_never_contains_prompt_or_response_text(
        self, mock_query: MagicMock
    ) -> None:
        distinctive_prompt = "DISTINCTIVE_PROMPT_PAYLOAD_ABC123"
        distinctive_assistant_text = "DISTINCTIVE_ASSISTANT_CONTENT_DEF456"
        distinctive_result_text = "DISTINCTIVE_RESULT_OUTPUT_GHI789"
        mock_query.side_effect = self._create_fake_query(
            [
                AssistantMessage(
                    content=[TextBlock(text=distinctive_assistant_text)],
                    model=self.model_name,
                ),
                ResultMessage(
                    subtype="execution_failure",
                    duration_ms=50,
                    duration_api_ms=50,
                    is_error=True,
                    num_turns=1,
                    session_id="test-session-identifier",
                    result=distinctive_result_text,
                    api_error_status=500,
                    errors=["internal_error"],
                ),
            ]
        )

        with self.assertRaises(LanguageModelUnavailable) as context:
            self.adapter.generate(prompt=distinctive_prompt)

        self.assertIsInstance(context.exception.__cause__, ClaudeBackendReportedError)
        cause_message = str(context.exception.__cause__)
        self.assertNotIn(distinctive_prompt, cause_message)
        self.assertNotIn(distinctive_assistant_text, cause_message)
        self.assertNotIn(distinctive_result_text, cause_message)

    @patch("src.infrastructure.adapters.llm_generator.claude_generator_adapter.query")
    def test_generate_with_usage_raises_language_model_unavailable_with_cause_on_assistant_error(
        self, mock_query: MagicMock
    ) -> None:
        mock_query.side_effect = self._create_fake_query(
            [
                AssistantMessage(
                    content=[TextBlock(text="API error")],
                    model=self.model_name,
                    error="rate_limit",
                ),
            ]
        )

        with self.assertRaises(LanguageModelUnavailable) as context:
            self.adapter.generate_with_usage(prompt=self.sample_prompt)

        self.assertIsInstance(context.exception.__cause__, ClaudeBackendReportedError)
        self.assertEqual(str(context.exception.__cause__), "assistant error: rate_limit")

    @patch("src.infrastructure.adapters.llm_generator.claude_generator_adapter.query")
    def test_generate_with_usage_raises_language_model_unavailable_with_cause_on_result_error(
        self, mock_query: MagicMock
    ) -> None:
        mock_query.side_effect = self._create_fake_query(
            [
                ResultMessage(
                    subtype="error_during_execution",
                    duration_ms=50,
                    duration_api_ms=50,
                    is_error=True,
                    num_turns=1,
                    session_id="test-session-identifier",
                    api_error_status=429,
                    errors=["quota exceeded"],
                ),
            ]
        )

        with self.assertRaises(LanguageModelUnavailable) as context:
            self.adapter.generate_with_usage(prompt=self.sample_prompt)

        self.assertIsInstance(context.exception.__cause__, ClaudeBackendReportedError)
        self.assertEqual(
            str(context.exception.__cause__),
            "result error: subtype=error_during_execution, api_error_status=429, errors=['quota exceeded']",
        )

    @patch("src.infrastructure.adapters.llm_generator.claude_generator_adapter.query")
    def test_generate_with_usage_raises_language_model_unavailable_on_sdk_error(
        self, mock_query: MagicMock
    ) -> None:
        backend_error = ProcessError("Process crashed", exit_code=2)
        mock_query.side_effect = self._create_failing_query(backend_error)

        with self.assertRaises(LanguageModelUnavailable) as context:
            self.adapter.generate_with_usage(prompt=self.sample_prompt)

        self.assertIs(context.exception.__cause__, backend_error)

    @patch("src.infrastructure.adapters.llm_generator.claude_generator_adapter.query")
    def test_generate_with_usage_sets_prompt_tokens_to_none_when_input_tokens_is_float(
        self, mock_query: MagicMock
    ) -> None:
        mock_query.side_effect = self._create_fake_query(
            [
                ResultMessage(
                    subtype="success",
                    duration_ms=100,
                    duration_api_ms=90,
                    is_error=False,
                    num_turns=1,
                    session_id="test-session-identifier",
                    usage={"input_tokens": 12.5, "output_tokens": 10},
                ),
            ]
        )

        result = self.adapter.generate_with_usage(prompt=self.sample_prompt)

        self.assertIsNone(result.prompt_tokens)
        self.assertEqual(result.completion_tokens, 10)

    @patch("src.infrastructure.adapters.llm_generator.claude_generator_adapter.query")
    def test_generate_with_usage_sets_prompt_tokens_to_none_when_input_tokens_is_string(
        self, mock_query: MagicMock
    ) -> None:
        mock_query.side_effect = self._create_fake_query(
            [
                ResultMessage(
                    subtype="success",
                    duration_ms=100,
                    duration_api_ms=90,
                    is_error=False,
                    num_turns=1,
                    session_id="test-session-identifier",
                    usage={"input_tokens": "128", "output_tokens": 10},
                ),
            ]
        )

        result = self.adapter.generate_with_usage(prompt=self.sample_prompt)

        self.assertIsNone(result.prompt_tokens)
        self.assertEqual(result.completion_tokens, 10)

    @patch("src.infrastructure.adapters.llm_generator.claude_generator_adapter.query")
    def test_generate_with_usage_sets_prompt_tokens_to_none_when_input_tokens_is_boolean(
        self, mock_query: MagicMock
    ) -> None:
        for boolean_value in (True, False):
            mock_query.side_effect = self._create_fake_query(
                [
                    ResultMessage(
                        subtype="success",
                        duration_ms=100,
                        duration_api_ms=90,
                        is_error=False,
                        num_turns=1,
                        session_id="test-session-identifier",
                        usage={"input_tokens": boolean_value, "output_tokens": 10},
                    ),
                ]
            )

            result = self.adapter.generate_with_usage(prompt=self.sample_prompt)

            self.assertIsNone(result.prompt_tokens)
            self.assertEqual(result.completion_tokens, 10)

    @patch("src.infrastructure.adapters.llm_generator.claude_generator_adapter.query")
    def test_generate_with_usage_sets_prompt_tokens_to_none_when_input_tokens_is_nested_dict(
        self, mock_query: MagicMock
    ) -> None:
        mock_query.side_effect = self._create_fake_query(
            [
                ResultMessage(
                    subtype="success",
                    duration_ms=100,
                    duration_api_ms=90,
                    is_error=False,
                    num_turns=1,
                    session_id="test-session-identifier",
                    usage={"input_tokens": {"count": 128}, "output_tokens": 10},
                ),
            ]
        )

        result = self.adapter.generate_with_usage(prompt=self.sample_prompt)

        self.assertIsNone(result.prompt_tokens)
        self.assertEqual(result.completion_tokens, 10)

    @patch("src.infrastructure.adapters.llm_generator.claude_generator_adapter.query")
    def test_generate_with_usage_sets_prompt_tokens_to_none_when_input_tokens_is_none(
        self, mock_query: MagicMock
    ) -> None:
        mock_query.side_effect = self._create_fake_query(
            [
                ResultMessage(
                    subtype="success",
                    duration_ms=100,
                    duration_api_ms=90,
                    is_error=False,
                    num_turns=1,
                    session_id="test-session-identifier",
                    usage={"input_tokens": None, "output_tokens": 10},
                ),
            ]
        )

        result = self.adapter.generate_with_usage(prompt=self.sample_prompt)

        self.assertIsNone(result.prompt_tokens)
        self.assertEqual(result.completion_tokens, 10)

    @patch("src.infrastructure.adapters.llm_generator.claude_generator_adapter.query")
    def test_generate_with_usage_sets_completion_tokens_to_none_when_output_tokens_is_float(
        self, mock_query: MagicMock
    ) -> None:
        mock_query.side_effect = self._create_fake_query(
            [
                ResultMessage(
                    subtype="success",
                    duration_ms=100,
                    duration_api_ms=90,
                    is_error=False,
                    num_turns=1,
                    session_id="test-session-identifier",
                    usage={"input_tokens": 10, "output_tokens": 64.5},
                ),
            ]
        )

        result = self.adapter.generate_with_usage(prompt=self.sample_prompt)

        self.assertEqual(result.prompt_tokens, 10)
        self.assertIsNone(result.completion_tokens)

    @patch("src.infrastructure.adapters.llm_generator.claude_generator_adapter.query")
    def test_generate_with_usage_sets_completion_tokens_to_none_when_output_tokens_is_string(
        self, mock_query: MagicMock
    ) -> None:
        mock_query.side_effect = self._create_fake_query(
            [
                ResultMessage(
                    subtype="success",
                    duration_ms=100,
                    duration_api_ms=90,
                    is_error=False,
                    num_turns=1,
                    session_id="test-session-identifier",
                    usage={"input_tokens": 10, "output_tokens": "64"},
                ),
            ]
        )

        result = self.adapter.generate_with_usage(prompt=self.sample_prompt)

        self.assertEqual(result.prompt_tokens, 10)
        self.assertIsNone(result.completion_tokens)

    @patch("src.infrastructure.adapters.llm_generator.claude_generator_adapter.query")
    def test_generate_with_usage_sets_completion_tokens_to_none_when_output_tokens_is_boolean(
        self, mock_query: MagicMock
    ) -> None:
        for boolean_value in (True, False):
            mock_query.side_effect = self._create_fake_query(
                [
                    ResultMessage(
                        subtype="success",
                        duration_ms=100,
                        duration_api_ms=90,
                        is_error=False,
                        num_turns=1,
                        session_id="test-session-identifier",
                        usage={"input_tokens": 10, "output_tokens": boolean_value},
                    ),
                ]
            )

            result = self.adapter.generate_with_usage(prompt=self.sample_prompt)

            self.assertEqual(result.prompt_tokens, 10)
            self.assertIsNone(result.completion_tokens)

    @patch("src.infrastructure.adapters.llm_generator.claude_generator_adapter.query")
    def test_generate_with_usage_sets_completion_tokens_to_none_when_output_tokens_is_nested_dict(
        self, mock_query: MagicMock
    ) -> None:
        mock_query.side_effect = self._create_fake_query(
            [
                ResultMessage(
                    subtype="success",
                    duration_ms=100,
                    duration_api_ms=90,
                    is_error=False,
                    num_turns=1,
                    session_id="test-session-identifier",
                    usage={"input_tokens": 10, "output_tokens": {"count": 64}},
                ),
            ]
        )

        result = self.adapter.generate_with_usage(prompt=self.sample_prompt)

        self.assertEqual(result.prompt_tokens, 10)
        self.assertIsNone(result.completion_tokens)

    @patch("src.infrastructure.adapters.llm_generator.claude_generator_adapter.query")
    def test_generate_with_usage_sets_completion_tokens_to_none_when_output_tokens_is_none(
        self, mock_query: MagicMock
    ) -> None:
        mock_query.side_effect = self._create_fake_query(
            [
                ResultMessage(
                    subtype="success",
                    duration_ms=100,
                    duration_api_ms=90,
                    is_error=False,
                    num_turns=1,
                    session_id="test-session-identifier",
                    usage={"input_tokens": 10, "output_tokens": None},
                ),
            ]
        )

        result = self.adapter.generate_with_usage(prompt=self.sample_prompt)

        self.assertEqual(result.prompt_tokens, 10)
        self.assertIsNone(result.completion_tokens)

    @patch("src.infrastructure.adapters.llm_generator.claude_generator_adapter.query")
    def test_generate_with_usage_preserves_zero_token_counts(self, mock_query: MagicMock) -> None:
        mock_query.side_effect = self._create_fake_query(
            [
                ResultMessage(
                    subtype="success",
                    duration_ms=100,
                    duration_api_ms=90,
                    is_error=False,
                    num_turns=1,
                    session_id="test-session-identifier",
                    usage={"input_tokens": 0, "output_tokens": 0},
                ),
            ]
        )

        result = self.adapter.generate_with_usage(prompt=self.sample_prompt)

        self.assertEqual(result.prompt_tokens, 0)
        self.assertEqual(result.completion_tokens, 0)

    @patch("src.infrastructure.adapters.llm_generator.claude_generator_adapter.query")
    def test_generate_with_usage_returns_none_tokens_when_usage_is_not_a_dictionary(
        self, mock_query: MagicMock
    ) -> None:
        mock_query.side_effect = self._create_fake_query(
            [
                ResultMessage(
                    subtype="success",
                    duration_ms=100,
                    duration_api_ms=90,
                    is_error=False,
                    num_turns=1,
                    session_id="test-session-identifier",
                    usage=cast(Any, "unexpected-usage-payload"),
                ),
            ]
        )

        result = self.adapter.generate_with_usage(prompt=self.sample_prompt)

        self.assertIsNone(result.prompt_tokens)
        self.assertIsNone(result.completion_tokens)

    @patch("src.infrastructure.adapters.llm_generator.claude_generator_adapter.query")
    def test_generate_with_usage_sums_input_and_cache_read_and_cache_creation_tokens(
        self, mock_query: MagicMock
    ) -> None:
        mock_query.side_effect = self._create_fake_query(
            [
                ResultMessage(
                    subtype="success",
                    duration_ms=100,
                    duration_api_ms=90,
                    is_error=False,
                    num_turns=1,
                    session_id="test-session-identifier",
                    usage={
                        "input_tokens": 100,
                        "cache_read_input_tokens": 20,
                        "cache_creation_input_tokens": 30,
                        "output_tokens": 50,
                    },
                ),
            ]
        )

        result = self.adapter.generate_with_usage(prompt=self.sample_prompt)

        self.assertEqual(result.prompt_tokens, 150)
        self.assertEqual(result.completion_tokens, 50)

    @patch("src.infrastructure.adapters.llm_generator.claude_generator_adapter.query")
    def test_generate_with_usage_sums_input_tokens_when_only_cache_read_is_present(
        self, mock_query: MagicMock
    ) -> None:
        mock_query.side_effect = self._create_fake_query(
            [
                ResultMessage(
                    subtype="success",
                    duration_ms=100,
                    duration_api_ms=90,
                    is_error=False,
                    num_turns=1,
                    session_id="test-session-identifier",
                    usage={
                        "input_tokens": 100,
                        "cache_read_input_tokens": 25,
                        "output_tokens": 50,
                    },
                ),
            ]
        )

        result = self.adapter.generate_with_usage(prompt=self.sample_prompt)

        self.assertEqual(result.prompt_tokens, 125)
        self.assertEqual(result.completion_tokens, 50)

    @patch("src.infrastructure.adapters.llm_generator.claude_generator_adapter.query")
    def test_generate_with_usage_sums_input_tokens_when_only_cache_creation_is_present(
        self, mock_query: MagicMock
    ) -> None:
        mock_query.side_effect = self._create_fake_query(
            [
                ResultMessage(
                    subtype="success",
                    duration_ms=100,
                    duration_api_ms=90,
                    is_error=False,
                    num_turns=1,
                    session_id="test-session-identifier",
                    usage={
                        "input_tokens": 100,
                        "cache_creation_input_tokens": 35,
                        "output_tokens": 50,
                    },
                ),
            ]
        )

        result = self.adapter.generate_with_usage(prompt=self.sample_prompt)

        self.assertEqual(result.prompt_tokens, 135)
        self.assertEqual(result.completion_tokens, 50)

    @patch("src.infrastructure.adapters.llm_generator.claude_generator_adapter.query")
    def test_generate_with_usage_uses_only_input_tokens_when_cache_keys_are_absent(
        self, mock_query: MagicMock
    ) -> None:
        mock_query.side_effect = self._create_fake_query(
            [
                ResultMessage(
                    subtype="success",
                    duration_ms=100,
                    duration_api_ms=90,
                    is_error=False,
                    num_turns=1,
                    session_id="test-session-identifier",
                    usage={
                        "input_tokens": 100,
                        "output_tokens": 50,
                    },
                ),
            ]
        )

        result = self.adapter.generate_with_usage(prompt=self.sample_prompt)

        self.assertEqual(result.prompt_tokens, 100)
        self.assertEqual(result.completion_tokens, 50)

    @patch("src.infrastructure.adapters.llm_generator.claude_generator_adapter.query")
    def test_generate_with_usage_treats_invalid_type_cache_keys_as_zero(
        self, mock_query: MagicMock
    ) -> None:
        invalid_cache_values = [
            "invalid_string",
            12.5,
            True,
            False,
            None,
            {"nested": 10},
            [10],
        ]
        for invalid_cache_value in invalid_cache_values:
            mock_query.side_effect = self._create_fake_query(
                [
                    ResultMessage(
                        subtype="success",
                        duration_ms=100,
                        duration_api_ms=90,
                        is_error=False,
                        num_turns=1,
                        session_id="test-session-identifier",
                        usage={
                            "input_tokens": 100,
                            "cache_read_input_tokens": invalid_cache_value,
                            "cache_creation_input_tokens": invalid_cache_value,
                            "output_tokens": 50,
                        },
                    ),
                ]
            )

            result = self.adapter.generate_with_usage(prompt=self.sample_prompt)

            self.assertEqual(result.prompt_tokens, 100)
            self.assertEqual(result.completion_tokens, 50)

    @patch("src.infrastructure.adapters.llm_generator.claude_generator_adapter.query")
    def test_generate_with_usage_returns_none_prompt_tokens_when_input_tokens_is_missing_despite_valid_cache_keys(
        self, mock_query: MagicMock
    ) -> None:
        mock_query.side_effect = self._create_fake_query(
            [
                ResultMessage(
                    subtype="success",
                    duration_ms=100,
                    duration_api_ms=90,
                    is_error=False,
                    num_turns=1,
                    session_id="test-session-identifier",
                    usage={
                        "cache_read_input_tokens": 20,
                        "cache_creation_input_tokens": 30,
                        "output_tokens": 50,
                    },
                ),
            ]
        )

        result = self.adapter.generate_with_usage(prompt=self.sample_prompt)

        self.assertIsNone(result.prompt_tokens)
        self.assertEqual(result.completion_tokens, 50)

    @patch("src.infrastructure.adapters.llm_generator.claude_generator_adapter.query")
    def test_generate_with_usage_returns_none_prompt_tokens_when_input_tokens_is_invalid_despite_valid_cache_keys(
        self, mock_query: MagicMock
    ) -> None:
        invalid_input_token_values = [
            "100",
            12.5,
            True,
            False,
            None,
            {"count": 100},
            [100],
        ]
        for invalid_input_token_value in invalid_input_token_values:
            mock_query.side_effect = self._create_fake_query(
                [
                    ResultMessage(
                        subtype="success",
                        duration_ms=100,
                        duration_api_ms=90,
                        is_error=False,
                        num_turns=1,
                        session_id="test-session-identifier",
                        usage={
                            "input_tokens": invalid_input_token_value,
                            "cache_read_input_tokens": 20,
                            "cache_creation_input_tokens": 30,
                            "output_tokens": 50,
                        },
                    ),
                ]
            )

            result = self.adapter.generate_with_usage(prompt=self.sample_prompt)

            self.assertIsNone(result.prompt_tokens)
            self.assertEqual(result.completion_tokens, 50)

    @patch("src.infrastructure.adapters.llm_generator.claude_generator_adapter.query")
    def test_generate_with_usage_preserves_zero_values_for_input_and_cache_tokens(
        self, mock_query: MagicMock
    ) -> None:
        mock_query.side_effect = self._create_fake_query(
            [
                ResultMessage(
                    subtype="success",
                    duration_ms=100,
                    duration_api_ms=90,
                    is_error=False,
                    num_turns=1,
                    session_id="test-session-identifier",
                    usage={
                        "input_tokens": 0,
                        "cache_read_input_tokens": 0,
                        "cache_creation_input_tokens": 0,
                        "output_tokens": 0,
                    },
                ),
            ]
        )

        result = self.adapter.generate_with_usage(prompt=self.sample_prompt)

        self.assertEqual(result.prompt_tokens, 0)
        self.assertEqual(result.completion_tokens, 0)
