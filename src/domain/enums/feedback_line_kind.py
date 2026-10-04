from enum import Enum


class FeedbackLineKind(Enum):
    """Categorizes the syntactic kind of a feedback line."""

    HEADING = "heading"
    BOLD_TITLE = "bold_title"
    PLAIN_TITLE = "plain_title"
    BULLET = "bullet"
    NUMBERED = "numbered"
    TABLE_ROW = "table_row"
    HORIZONTAL_RULE = "horizontal_rule"
    TEXT = "text"
