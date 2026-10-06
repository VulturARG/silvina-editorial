from typing import Any

from claude_agent_sdk import AssistantMessage, RateLimitEvent, ResultMessage

TEXT_PREVIEW_LENGTH = 200


class ClaudeMessageDigestBuilder:
    """Builds one-line diagnostic summaries of the messages streamed by the Claude Agent SDK."""

    def describe(self, message: Any) -> str:
        """Return a compact description of the message without its full payload."""
        if isinstance(message, AssistantMessage):
            return self._describe_assistant_message(message)
        if isinstance(message, ResultMessage):
            return self._describe_result_message(message)
        if isinstance(message, RateLimitEvent):
            return self._describe_rate_limit_event(message)
        subtype = getattr(message, "subtype", None)
        description = type(message).__name__
        if subtype is not None:
            description += f" subtype={subtype}"
        return description

    def _describe_assistant_message(self, message: AssistantMessage) -> str:
        blocks = ", ".join(self._describe_block(block) for block in message.content)
        return (
            f"AssistantMessage model={message.model} stop_reason={message.stop_reason} "
            f"error={message.error} usage={message.usage} blocks=[{blocks}]"
        )

    def _describe_block(self, block: Any) -> str:
        block_name = type(block).__name__
        text = getattr(block, "text", None)
        if isinstance(text, str):
            return f"{block_name}(length={len(text)}, preview={text[:TEXT_PREVIEW_LENGTH]!r})"
        tool_name = getattr(block, "name", None)
        if tool_name is not None:
            return f"{block_name}(name={tool_name!r})"
        return block_name

    def _describe_result_message(self, message: ResultMessage) -> str:
        return (
            f"ResultMessage subtype={message.subtype} is_error={message.is_error} "
            f"num_turns={message.num_turns} stop_reason={message.stop_reason} "
            f"terminal_reason={message.terminal_reason} "
            f"api_error_status={message.api_error_status} errors={message.errors} "
            f"permission_denials={message.permission_denials} "
            f"deferred_tool_use={message.deferred_tool_use} "
            f"duration_ms={message.duration_ms} usage={message.usage}"
        )

    def _describe_rate_limit_event(self, message: RateLimitEvent) -> str:
        rate_limit_info = message.rate_limit_info
        return (
            f"RateLimitEvent status={rate_limit_info.status} "
            f"rate_limit_type={rate_limit_info.rate_limit_type} "
            f"resets_at={rate_limit_info.resets_at}"
        )
