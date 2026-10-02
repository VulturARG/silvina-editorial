from collections.abc import AsyncIterator
from typing import Any
from unittest import TestCase
from unittest.mock import MagicMock, patch

from claude_agent_sdk import (
    AssistantMessage,
    CLIConnectionError,
    CLINotFoundError,
    ClaudeAgentOptions,
    ClaudeSDKError,
    ProcessError,
    ResultMessage,
    TextBlock,
    ThinkingBlock,
)

from src.domain.dtos.llm_generation_dto import LlmGenerationDTO
from src.domain.enums.llm_done_reason import LlmDoneReason
from src.domain.exceptions.language_model_errors import LanguageModelUnavailable
from src.infrastructure.adapters.llm_generator.claude_generator_adapter import (
    ClaudeGeneratorAdapter,
)


class TestClaudeGeneratorAdapter(TestCase):
    """Unit tests for the ClaudeGeneratorAdapter class."""

    def setUp(self) -> None:
        self.model_name = "claude-sonnet-4-5-20250929"
        self.sample_prompt = "Analyze this text"
        self.sample_options = {"temperature": 0.2, "num_predict": 500}
        self.adapter = ClaudeGeneratorAdapter(model_name=self.model_name)

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
            env={"ANTHROPIC_API_KEY": ""},
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
            env={"ANTHROPIC_API_KEY": ""},
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
            env={"ANTHROPIC_API_KEY": ""},
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

        with self.assertRaises(LanguageModelUnavailable):
            self.adapter.generate(prompt=self.sample_prompt)

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

        with self.assertRaises(LanguageModelUnavailable):
            self.adapter.generate(prompt=self.sample_prompt)

    @patch("src.infrastructure.adapters.llm_generator.claude_generator_adapter.query")
    def test_generate_with_usage_raises_language_model_unavailable_on_sdk_error(
        self, mock_query: MagicMock
    ) -> None:
        backend_error = ProcessError("Process crashed", exit_code=2)
        mock_query.side_effect = self._create_failing_query(backend_error)

        with self.assertRaises(LanguageModelUnavailable) as context:
            self.adapter.generate_with_usage(prompt=self.sample_prompt)

        self.assertIs(context.exception.__cause__, backend_error)
