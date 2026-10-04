from collections.abc import Sequence
from re import Match, compile

from src.domain.dtos.classified_feedback_line_dto import ClassifiedFeedbackLineDTO
from src.domain.dtos.feedback_line_dto import FeedbackLineDTO
from src.domain.enums.feedback_line_kind import FeedbackLineKind
from src.domain.quality.feedback_list_marker import FeedbackListMarker

_HORIZONTAL_RULE_PATTERN = compile(r"^(?:(?:-[ \t]*){3,}|(?:\*[ \t]*){3,}|(?:_[ \t]*){3,})$")
_BLOCKQUOTE_MARKER_PATTERN = compile(r"^[ \t]*>[ \t]*")
_HEADING_LINE_PATTERN = compile(r"^(#{1,6})\s+(.*)$")
_BOLD_TITLE_LINE_PATTERN = compile(r"^\*\*([^*]+)\*\*:?$")
_BULLET_ITEM_PATTERN = compile(r"^([-*+])[ \t]+(.*)$")
_NUMBERED_ITEM_PATTERN = compile(r"^(\d+)\.[ \t]+(.*)$")
_MAXIMUM_PLAIN_TITLE_LENGTH = 60
_SENTENCE_TERMINAL_PUNCTUATION = (".", "!", "?")


class FeedbackLineClassifier:
    """Prepares and classifies feedback lines into structural line kinds."""

    def prepare_lines(self, lines: Sequence[str]) -> list[FeedbackLineDTO]:
        """Convert raw markdown lines into prepared lines with calculated indentation."""
        return [self.prepare_line(raw_line) for raw_line in lines]

    def prepare_line(self, raw_line: str) -> FeedbackLineDTO:
        """Prepare a single raw line by removing blockquotes and measuring indentation."""
        line_without_blockquote = _BLOCKQUOTE_MARKER_PATTERN.sub("", raw_line)
        stripped_line = line_without_blockquote.strip()
        indentation = (
            len(line_without_blockquote) - len(line_without_blockquote.lstrip())
            if stripped_line
            else 0
        )
        return FeedbackLineDTO(text=stripped_line, indentation=indentation)

    def find_next_non_empty_line(
        self, lines: Sequence[FeedbackLineDTO], current_index: int
    ) -> FeedbackLineDTO | None:
        """Find the next non-empty line after current_index using forward lookup."""
        for future_index in range(current_index + 1, len(lines)):
            future_line = lines[future_index]
            if future_line.text:
                return future_line
        return None

    def classify(
        self,
        line: FeedbackLineDTO,
        next_line: FeedbackLineDTO | None = None,
        is_preceded_by_blank: bool = False,
    ) -> ClassifiedFeedbackLineDTO:
        """Classify a single prepared feedback line into its syntactic kind with extracted payload."""
        title_candidate = self._classify_heading_or_title(line, next_line, is_preceded_by_blank)
        if title_candidate is not None:
            return title_candidate
        return self._classify_item_or_text(line, next_line)

    def is_list_item_text(self, text: str) -> bool:
        """Check whether the given text matches bullet or numbered list item syntax."""
        return (
            _BULLET_ITEM_PATTERN.match(text) is not None
            or _NUMBERED_ITEM_PATTERN.match(text) is not None
        )

    def _classify_heading_or_title(
        self,
        line: FeedbackLineDTO,
        next_line: FeedbackLineDTO | None,
        is_preceded_by_blank: bool,
    ) -> ClassifiedFeedbackLineDTO | None:
        text = line.text
        if _HORIZONTAL_RULE_PATTERN.match(text) is not None:
            return ClassifiedFeedbackLineDTO(kind=FeedbackLineKind.HORIZONTAL_RULE, line=line)
        if text.startswith("|"):
            return ClassifiedFeedbackLineDTO(kind=FeedbackLineKind.TABLE_ROW, line=line)
        heading_match = _HEADING_LINE_PATTERN.match(text)
        if heading_match is not None:
            return self._build_heading_dto(line, heading_match)
        if _BOLD_TITLE_LINE_PATTERN.match(text) is not None:
            return ClassifiedFeedbackLineDTO(
                kind=FeedbackLineKind.BOLD_TITLE, line=line, title_text=text
            )
        if self._is_plain_line_title(line, next_line, is_preceded_by_blank):
            return ClassifiedFeedbackLineDTO(
                kind=FeedbackLineKind.PLAIN_TITLE, line=line, title_text=text
            )
        return None

    def _classify_item_or_text(
        self,
        line: FeedbackLineDTO,
        next_line: FeedbackLineDTO | None,
    ) -> ClassifiedFeedbackLineDTO:
        text = line.text
        bullet_match = _BULLET_ITEM_PATTERN.match(text)
        if bullet_match is not None:
            return self._build_bullet_dto(line, next_line, bullet_match)
        numbered_match = _NUMBERED_ITEM_PATTERN.match(text)
        if numbered_match is not None:
            return self._build_numbered_dto(line, next_line, numbered_match)
        return self._build_text_dto(line, next_line)

    def _build_heading_dto(
        self, line: FeedbackLineDTO, match: Match[str]
    ) -> ClassifiedFeedbackLineDTO:
        return ClassifiedFeedbackLineDTO(
            kind=FeedbackLineKind.HEADING,
            line=line,
            title_text=match.group(2),
            heading_level=len(match.group(1)),
        )

    def _build_bullet_dto(
        self,
        line: FeedbackLineDTO,
        next_line: FeedbackLineDTO | None,
        match: Match[str],
    ) -> ClassifiedFeedbackLineDTO:
        starts_children = self._starts_unindented_children(line, next_line, is_list_item=True)
        return ClassifiedFeedbackLineDTO(
            kind=FeedbackLineKind.BULLET,
            line=line,
            list_marker=FeedbackListMarker.BULLET,
            item_content=match.group(2),
            starts_unindented_children=starts_children,
        )

    def _build_numbered_dto(
        self,
        line: FeedbackLineDTO,
        next_line: FeedbackLineDTO | None,
        match: Match[str],
    ) -> ClassifiedFeedbackLineDTO:
        starts_children = self._starts_unindented_children(line, next_line, is_list_item=True)
        marker = FeedbackListMarker.format_numbered(match.group(1))
        return ClassifiedFeedbackLineDTO(
            kind=FeedbackLineKind.NUMBERED,
            line=line,
            list_marker=marker,
            item_content=match.group(2),
            starts_unindented_children=starts_children,
        )

    def _build_text_dto(
        self,
        line: FeedbackLineDTO,
        next_line: FeedbackLineDTO | None,
    ) -> ClassifiedFeedbackLineDTO:
        starts_children = self._starts_unindented_children(line, next_line, is_list_item=False)
        return ClassifiedFeedbackLineDTO(
            kind=FeedbackLineKind.TEXT,
            line=line,
            item_content=line.text,
            starts_unindented_children=starts_children,
        )

    def _starts_unindented_children(
        self,
        line: FeedbackLineDTO,
        next_line: FeedbackLineDTO | None,
        is_list_item: bool,
    ) -> bool:
        stripped_without_bold = line.text.replace("**", "").strip()
        if not stripped_without_bold.endswith(":"):
            return False
        if next_line is None:
            return False
        if not self.is_list_item_text(next_line.text):
            return False
        if is_list_item:
            return next_line.indentation <= line.indentation
        return True

    def _is_plain_line_title(
        self,
        line: FeedbackLineDTO,
        next_line: FeedbackLineDTO | None,
        is_preceded_by_blank: bool,
    ) -> bool:
        if not is_preceded_by_blank:
            return False
        predicates = (
            self._has_colon_suffix,
            self._has_valid_plain_title_length,
            self._is_not_list_item,
            self._is_not_bold_prefixed,
            self._has_no_inner_terminal_punctuation,
        )
        for predicate in predicates:
            if not predicate(line.text):
                return False
        return self._is_followed_by_list_item(next_line)

    def _has_colon_suffix(self, text: str) -> bool:
        return text.endswith(":")

    def _has_valid_plain_title_length(self, text: str) -> bool:
        return len(text) <= _MAXIMUM_PLAIN_TITLE_LENGTH

    def _is_not_list_item(self, text: str) -> bool:
        return not self.is_list_item_text(text)

    def _is_not_bold_prefixed(self, text: str) -> bool:
        return not text.startswith("**")

    def _has_no_inner_terminal_punctuation(self, text: str) -> bool:
        return not any(punctuation in text[:-1] for punctuation in _SENTENCE_TERMINAL_PUNCTUATION)

    def _is_followed_by_list_item(self, next_line: FeedbackLineDTO | None) -> bool:
        if next_line is None:
            return False
        return self.is_list_item_text(next_line.text)
