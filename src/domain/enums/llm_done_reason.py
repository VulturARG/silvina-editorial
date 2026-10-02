from enum import Enum


class LlmDoneReason(str, Enum):
    """Reason why the language model backend terminated generation."""

    STOP = "stop"
    LENGTH = "length"
