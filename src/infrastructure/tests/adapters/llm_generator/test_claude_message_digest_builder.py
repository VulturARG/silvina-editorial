from unittest import TestCase

from claude_agent_sdk import (
    AssistantMessage,
    RateLimitEvent,
    RateLimitInfo,
    ResultMessage,
    SystemMessage,
    TextBlock,
    ToolUseBlock,
)

from src.infrastructure.adapters.llm_generator.claude_message_digest_builder import (
    ClaudeMessageDigestBuilder,
)


class TestClaudeMessageDigestBuilder(TestCase):
    def setUp(self) -> None:
        self.builder = ClaudeMessageDigestBuilder()

    def test_describes_assistant_message_with_text_and_tool_blocks(self) -> None:
        message = AssistantMessage(
            content=[
                TextBlock(text="Primera respuesta del modelo"),
                ToolUseBlock(id="tool-1", name="Read", input={"file_path": "x"}),
            ],
            model="claude-haiku-4-5-20251001",
            stop_reason="tool_use",
        )

        digest = self.builder.describe(message)

        self.assertIn("AssistantMessage", digest)
        self.assertIn("model=claude-haiku-4-5-20251001", digest)
        self.assertIn("stop_reason=tool_use", digest)
        self.assertIn("TextBlock(length=28, preview='Primera respuesta del modelo')", digest)
        self.assertIn("ToolUseBlock(name='Read')", digest)

    def test_truncates_long_text_preview(self) -> None:
        message = AssistantMessage(
            content=[TextBlock(text="a" * 500)],
            model="claude-haiku-4-5-20251001",
        )

        digest = self.builder.describe(message)

        self.assertIn("length=500", digest)
        self.assertNotIn("a" * 201, digest)

    def test_describes_result_message_fields(self) -> None:
        message = ResultMessage(
            subtype="error_max_turns",
            duration_ms=7000,
            duration_api_ms=6500,
            is_error=True,
            num_turns=2,
            session_id="session-identifier",
            stop_reason="tool_use",
            terminal_reason="max_turns",
            errors=["Reached maximum number of turns (1)"],
            permission_denials=[{"tool_name": "Bash"}],
            usage={"input_tokens": 10, "output_tokens": 5},
        )

        digest = self.builder.describe(message)

        self.assertIn("ResultMessage", digest)
        self.assertIn("subtype=error_max_turns", digest)
        self.assertIn("num_turns=2", digest)
        self.assertIn("stop_reason=tool_use", digest)
        self.assertIn("terminal_reason=max_turns", digest)
        self.assertIn("errors=['Reached maximum number of turns (1)']", digest)
        self.assertIn("permission_denials=[{'tool_name': 'Bash'}]", digest)
        self.assertIn("usage={'input_tokens': 10, 'output_tokens': 5}", digest)

    def test_describes_rate_limit_event_status(self) -> None:
        message = RateLimitEvent(
            rate_limit_info=RateLimitInfo(status="allowed_warning", rate_limit_type="five_hour"),
            uuid="event-identifier",
            session_id="session-identifier",
        )

        digest = self.builder.describe(message)

        self.assertIn("RateLimitEvent", digest)
        self.assertIn("status=allowed_warning", digest)
        self.assertIn("rate_limit_type=five_hour", digest)

    def test_describes_unknown_message_by_type_name_and_subtype(self) -> None:
        message = SystemMessage(subtype="init", data={"session_id": "session-identifier"})

        digest = self.builder.describe(message)

        self.assertEqual(digest, "SystemMessage subtype=init")
