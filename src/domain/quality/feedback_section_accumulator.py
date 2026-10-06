from src.domain.dtos.classified_feedback_line_dto import ClassifiedFeedbackLineDTO
from src.domain.dtos.feedback_block_dto import FeedbackBlockDTO


class FeedbackSectionAccumulator:
    """Accumulates titles, blocks, and completed sections during feedback parsing."""

    def __init__(self) -> None:
        self._sections: list[tuple[FeedbackBlockDTO | None, list[FeedbackBlockDTO]]] = []
        self._current_title: FeedbackBlockDTO | None = None
        self._current_blocks: list[FeedbackBlockDTO] = []
        self._previous_line_counts_as_blank = False
        self._has_seen_non_empty_line = False
        self._last_processed_line: ClassifiedFeedbackLineDTO | None = None

    def is_preceded_by_blank(self) -> bool:
        """Check whether the next line should be considered preceded by a blank line."""
        return not self._has_seen_non_empty_line or self._previous_line_counts_as_blank

    def mark_blank_line(self) -> None:
        """Record that a blank line was encountered."""
        self._previous_line_counts_as_blank = True

    def mark_non_empty_line(self) -> None:
        """Record that a non-empty line was encountered and reset blank line precedence."""
        self._has_seen_non_empty_line = True
        self._previous_line_counts_as_blank = False

    def set_previous_line_counts_as_blank(self, value: bool) -> None:
        """Explicitly set whether the preceding line counts as blank."""
        self._previous_line_counts_as_blank = value

    def record_table_row(self, line: ClassifiedFeedbackLineDTO) -> None:
        """Record a table row line and ensure preceding blank line state is cleared."""
        self._previous_line_counts_as_blank = False
        self._last_processed_line = line

    def open_title(self, title_block: FeedbackBlockDTO) -> None:
        """Close the active section if non-empty and start a new titled section."""
        self._close_current_section()
        self._current_title = title_block
        self._current_blocks = []

    def append_block(self, block: FeedbackBlockDTO) -> None:
        """Append a feedback block to the currently active section."""
        self._current_blocks.append(block)

    def finish(self) -> list[tuple[FeedbackBlockDTO | None, list[FeedbackBlockDTO]]]:
        """Close any remaining active section and return the collected sections."""
        self._close_current_section()
        return list(self._sections)

    def _close_current_section(self) -> None:
        if self._current_title is not None or self._current_blocks:
            self._sections.append((self._current_title, self._current_blocks))
            self._current_title = None
            self._current_blocks = []
