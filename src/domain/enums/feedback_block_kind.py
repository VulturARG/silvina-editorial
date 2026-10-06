from enum import Enum


class FeedbackBlockKind(Enum):
    """Categorizes the structural role of a block in parsed quality feedback."""

    TITLE = "title"
    ITEM = "item"
    TEXT = "text"
