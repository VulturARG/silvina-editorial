from src.domain.dtos.classified_feedback_line_dto import ClassifiedFeedbackLineDTO
from src.domain.dtos.feedback_block_dto import FeedbackBlockDTO
from src.domain.enums.feedback_block_kind import FeedbackBlockKind
from src.domain.enums.feedback_line_kind import FeedbackLineKind
from src.domain.quality.feedback_line_classifier import FeedbackLineClassifier
from src.domain.quality.feedback_parsing_state import FeedbackParsingState
from src.domain.quality.feedback_section_capper import FeedbackSectionCapper
from src.domain.quality.feedback_text_cleaner import FeedbackTextCleaner


class FeedbackStructureParser:
    """Parses raw dimension feedback lines into a sequence of structured blocks."""

    def __init__(
        self,
        classifier: FeedbackLineClassifier,
        capper: FeedbackSectionCapper,
        text_cleaner: FeedbackTextCleaner,
    ) -> None:
        self._classifier = classifier
        self._capper = capper
        self._text_cleaner = text_cleaner
        self._handlers = {
            FeedbackLineKind.HEADING: self._handle_heading,
            FeedbackLineKind.BOLD_TITLE: self._handle_bold_title,
            FeedbackLineKind.PLAIN_TITLE: self._handle_plain_title,
            FeedbackLineKind.BULLET: self._handle_bullet,
            FeedbackLineKind.NUMBERED: self._handle_numbered,
            FeedbackLineKind.TEXT: self._handle_text,
            FeedbackLineKind.TABLE_ROW: self._handle_table_row,
        }

    def parse(
        self, lines: list[str], dimension_heading_level: int = 0
    ) -> tuple[FeedbackBlockDTO, ...]:
        """Parse dimension lines into capped structured feedback blocks."""
        state = FeedbackParsingState()
        prepared_lines = self._classifier.prepare_lines(lines)

        for index, line in enumerate(prepared_lines):
            if not line.text:
                state.accumulator.mark_blank_line()
                continue
            lookahead = self._classifier.find_next_non_empty_line(prepared_lines, index)
            is_preceded = state.accumulator.is_preceded_by_blank()
            classified_line = self._classifier.classify(line, lookahead, is_preceded)
            state.accumulator.mark_non_empty_line()
            if self._should_stop(classified_line, dimension_heading_level):
                break
            handler = self._handlers[classified_line.kind]
            handler(classified_line, state)

        sections = state.accumulator.finish()
        return self._capper.cap_sections(sections)

    def _should_stop(
        self,
        line: ClassifiedFeedbackLineDTO,
        dimension_heading_level: int,
    ) -> bool:
        if line.kind == FeedbackLineKind.HORIZONTAL_RULE:
            return True
        if line.kind == FeedbackLineKind.HEADING and dimension_heading_level > 0:
            return line.heading_level <= dimension_heading_level
        return False

    def _open_title(
        self,
        raw_text: str,
        state: FeedbackParsingState,
    ) -> None:
        state.hierarchy_tracker.reset()
        title_block = FeedbackBlockDTO(
            kind=FeedbackBlockKind.TITLE,
            text=self._text_cleaner.clean_title_text(raw_text),
            level=0,
            marker="",
        )
        state.accumulator.open_title(title_block)

    def _handle_heading(
        self,
        line: ClassifiedFeedbackLineDTO,
        state: FeedbackParsingState,
    ) -> None:
        self._open_title(line.title_text, state)
        state.accumulator.set_previous_line_counts_as_blank(True)

    def _handle_bold_title(
        self,
        line: ClassifiedFeedbackLineDTO,
        state: FeedbackParsingState,
    ) -> None:
        self._open_title(line.title_text, state)
        state.accumulator.set_previous_line_counts_as_blank(True)

    def _handle_plain_title(
        self,
        line: ClassifiedFeedbackLineDTO,
        state: FeedbackParsingState,
    ) -> None:
        self._open_title(line.title_text, state)

    def _handle_bullet(
        self,
        line: ClassifiedFeedbackLineDTO,
        state: FeedbackParsingState,
    ) -> None:
        self._append_list_item(line, state)

    def _handle_numbered(
        self,
        line: ClassifiedFeedbackLineDTO,
        state: FeedbackParsingState,
    ) -> None:
        self._append_list_item(line, state)

    def _handle_text(
        self,
        line: ClassifiedFeedbackLineDTO,
        state: FeedbackParsingState,
    ) -> None:
        content = self._text_cleaner.clean_dangling_bold(line.item_content)
        if not content:
            return
        state.accumulator.append_block(
            FeedbackBlockDTO(
                kind=FeedbackBlockKind.TEXT,
                text=content,
                level=0,
                marker="",
            )
        )
        state.hierarchy_tracker.reset()
        if line.starts_unindented_children:
            state.hierarchy_tracker.enter_children_mode()

    def _handle_table_row(
        self,
        line: ClassifiedFeedbackLineDTO,
        state: FeedbackParsingState,
    ) -> None:
        state.accumulator.record_table_row(line)

    def _append_list_item(
        self,
        line: ClassifiedFeedbackLineDTO,
        state: FeedbackParsingState,
    ) -> None:
        content = self._text_cleaner.clean_dangling_bold(line.item_content)
        if not content:
            return
        level = state.hierarchy_tracker.determine_item_level(line.line.indentation)
        state.accumulator.append_block(
            FeedbackBlockDTO(
                kind=FeedbackBlockKind.ITEM,
                text=content,
                level=level,
                marker=line.list_marker,
            )
        )
        if (
            line.starts_unindented_children
            and not state.hierarchy_tracker.in_unindented_children_mode
        ):
            state.hierarchy_tracker.enter_children_mode()
