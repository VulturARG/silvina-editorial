from re import compile

from src.domain.dtos.feedback_block_dto import FeedbackBlockDTO
from src.domain.enums.feedback_block_kind import FeedbackBlockKind

_HORIZONTAL_RULE_PATTERN = compile(r"^(?:(?:-[ \t]*){3,}|(?:\*[ \t]*){3,}|(?:_[ \t]*){3,})$")
_BLOCKQUOTE_MARKER_PATTERN = compile(r"^[ \t]*>[ \t]*")
_HEADING_LINE_PATTERN = compile(r"^(#{1,6})\s+(.*)$")
_BOLD_TITLE_LINE_PATTERN = compile(r"^\*\*([^*]+)\*\*:?$")
_BULLET_ITEM_PATTERN = compile(r"^([-*+])[ \t]+(.*)$")
_NUMBERED_ITEM_PATTERN = compile(r"^(\d+)\.[ \t]+(.*)$")
_MAXIMUM_PLAIN_TITLE_LENGTH = 60
_SENTENCE_TERMINAL_PUNCTUATION = (".", "!", "?")


class FeedbackStructureParser:
    """Parses raw dimension feedback lines into a sequence of structured blocks."""

    def __init__(self, maximum_items_per_section: int = 8) -> None:
        self._maximum_items_per_section = maximum_items_per_section

    def parse(
        self, lines: list[str], dimension_heading_level: int = 0
    ) -> tuple[FeedbackBlockDTO, ...]:
        """Parse dimension lines into capped structured feedback blocks."""
        sections: list[tuple[FeedbackBlockDTO | None, list[FeedbackBlockDTO]]] = []
        current_title: FeedbackBlockDTO | None = None
        current_blocks: list[FeedbackBlockDTO] = []
        previous_top_level_indentation: int | None = None
        in_unindented_children_mode = False
        child_indentation: int | None = None
        has_seen_non_empty_line = False
        previous_line_was_blank = False

        prepared_lines: list[tuple[str, int]] = []
        for raw_line in lines:
            line_without_blockquote = _BLOCKQUOTE_MARKER_PATTERN.sub("", raw_line)
            stripped_line = line_without_blockquote.strip()
            indentation = (
                len(line_without_blockquote) - len(line_without_blockquote.lstrip())
                if stripped_line
                else 0
            )
            prepared_lines.append((stripped_line, indentation))

        for index, (stripped_line, indentation) in enumerate(prepared_lines):
            if not stripped_line:
                previous_line_was_blank = True
                continue

            if _HORIZONTAL_RULE_PATTERN.match(stripped_line) is not None:
                break

            if stripped_line.startswith("|"):
                previous_line_was_blank = False
                has_seen_non_empty_line = True
                continue

            is_preceded_by_blank_or_first = not has_seen_non_empty_line or previous_line_was_blank
            has_seen_non_empty_line = True
            previous_line_was_blank = False

            heading_match = _HEADING_LINE_PATTERN.match(stripped_line)
            if heading_match is not None:
                in_unindented_children_mode = False
                child_indentation = None
                heading_level = len(heading_match.group(1))
                if dimension_heading_level > 0 and heading_level <= dimension_heading_level:
                    break
                if current_title is not None or current_blocks:
                    sections.append((current_title, current_blocks))
                title_text = self._clean_title_text(heading_match.group(2))
                current_title = FeedbackBlockDTO(
                    kind=FeedbackBlockKind.TITLE,
                    text=title_text,
                    level=0,
                    marker="",
                )
                current_blocks = []
                previous_top_level_indentation = None
                continue

            bold_title_match = _BOLD_TITLE_LINE_PATTERN.match(stripped_line)
            if bold_title_match is not None:
                in_unindented_children_mode = False
                child_indentation = None
                if current_title is not None or current_blocks:
                    sections.append((current_title, current_blocks))
                title_text = self._clean_title_text(stripped_line)
                current_title = FeedbackBlockDTO(
                    kind=FeedbackBlockKind.TITLE,
                    text=title_text,
                    level=0,
                    marker="",
                )
                current_blocks = []
                previous_top_level_indentation = None
                continue

            next_non_empty = self._find_next_non_empty_line(prepared_lines, index)
            if self._is_plain_line_title(
                stripped_line, next_non_empty, is_preceded_by_blank_or_first
            ):
                in_unindented_children_mode = False
                child_indentation = None
                if current_title is not None or current_blocks:
                    sections.append((current_title, current_blocks))
                title_text = self._clean_title_text(stripped_line)
                current_title = FeedbackBlockDTO(
                    kind=FeedbackBlockKind.TITLE,
                    text=title_text,
                    level=0,
                    marker="",
                )
                current_blocks = []
                previous_top_level_indentation = None
                continue

            bullet_match = _BULLET_ITEM_PATTERN.match(stripped_line)
            numbered_match = _NUMBERED_ITEM_PATTERN.match(stripped_line)
            is_list_item = bullet_match is not None or numbered_match is not None

            if not is_list_item:
                in_unindented_children_mode = False
                child_indentation = None

            starts_unindented_children = self._line_starts_unindented_children(
                stripped_line, indentation, is_list_item, next_non_empty
            )

            if bullet_match is not None:
                content = self._clean_dangling_bold(bullet_match.group(2))
                if not content:
                    continue
                if in_unindented_children_mode:
                    if child_indentation is None:
                        child_indentation = indentation
                    if indentation > child_indentation:
                        level = 2
                    else:
                        level = 1
                elif (
                    previous_top_level_indentation is not None
                    and indentation > previous_top_level_indentation
                ):
                    level = 1
                else:
                    level = 0
                    previous_top_level_indentation = indentation
                current_blocks.append(
                    FeedbackBlockDTO(
                        kind=FeedbackBlockKind.ITEM,
                        text=content,
                        level=level,
                        marker="•",
                    )
                )
                if starts_unindented_children and not in_unindented_children_mode:
                    in_unindented_children_mode = True
                    child_indentation = None
                continue

            if numbered_match is not None:
                content = self._clean_dangling_bold(numbered_match.group(2))
                if not content:
                    continue
                if in_unindented_children_mode:
                    if child_indentation is None:
                        child_indentation = indentation
                    if indentation > child_indentation:
                        level = 2
                    else:
                        level = 1
                elif (
                    previous_top_level_indentation is not None
                    and indentation > previous_top_level_indentation
                ):
                    level = 1
                else:
                    level = 0
                    previous_top_level_indentation = indentation
                current_blocks.append(
                    FeedbackBlockDTO(
                        kind=FeedbackBlockKind.ITEM,
                        text=content,
                        level=level,
                        marker=f"{numbered_match.group(1)}.",
                    )
                )
                if starts_unindented_children and not in_unindented_children_mode:
                    in_unindented_children_mode = True
                    child_indentation = None
                continue

            content = self._clean_dangling_bold(stripped_line)
            if not content:
                continue
            current_blocks.append(
                FeedbackBlockDTO(
                    kind=FeedbackBlockKind.TEXT,
                    text=content,
                    level=0,
                    marker="",
                )
            )
            previous_top_level_indentation = None
            if starts_unindented_children:
                in_unindented_children_mode = True
                child_indentation = None

        if current_title is not None or current_blocks:
            sections.append((current_title, current_blocks))

        return self._cap_and_filter_sections(sections)

    def _cap_and_filter_sections(
        self,
        sections: list[tuple[FeedbackBlockDTO | None, list[FeedbackBlockDTO]]],
    ) -> tuple[FeedbackBlockDTO, ...]:
        result_blocks: list[FeedbackBlockDTO] = []

        for title, blocks in sections:
            kept_blocks: list[FeedbackBlockDTO] = []
            top_level_count = 0
            current_level_zero_parent_kept = True
            level_one_count_for_current_parent = 0
            current_level_one_parent_kept = False

            for block in blocks:
                if block.level == 0:
                    if top_level_count < self._maximum_items_per_section:
                        kept_blocks.append(block)
                        top_level_count += 1
                        current_level_zero_parent_kept = True
                    else:
                        current_level_zero_parent_kept = False
                    level_one_count_for_current_parent = 0
                    current_level_one_parent_kept = False
                elif block.level == 1:
                    if current_level_zero_parent_kept:
                        if level_one_count_for_current_parent < self._maximum_items_per_section:
                            kept_blocks.append(block)
                            level_one_count_for_current_parent += 1
                            current_level_one_parent_kept = True
                        else:
                            current_level_one_parent_kept = False
                    else:
                        current_level_one_parent_kept = False
                else:
                    if current_level_one_parent_kept:
                        kept_blocks.append(block)

            if title is not None:
                if kept_blocks:
                    result_blocks.append(title)
                    result_blocks.extend(kept_blocks)
            else:
                result_blocks.extend(kept_blocks)

        return tuple(result_blocks)

    def _is_plain_line_title(
        self,
        stripped_line: str,
        next_non_empty: tuple[str, int] | None,
        is_preceded_by_blank_or_first: bool,
    ) -> bool:
        if not is_preceded_by_blank_or_first:
            return False
        if not stripped_line.endswith(":"):
            return False
        if len(stripped_line) > _MAXIMUM_PLAIN_TITLE_LENGTH:
            return False
        if _BULLET_ITEM_PATTERN.match(stripped_line) is not None:
            return False
        if _NUMBERED_ITEM_PATTERN.match(stripped_line) is not None:
            return False
        if _HEADING_LINE_PATTERN.match(stripped_line) is not None:
            return False
        if _BOLD_TITLE_LINE_PATTERN.match(stripped_line) is not None:
            return False
        if stripped_line.startswith("**"):
            return False
        if any(punctuation in stripped_line[:-1] for punctuation in _SENTENCE_TERMINAL_PUNCTUATION):
            return False
        if next_non_empty is None:
            return False
        next_line_stripped, _ = next_non_empty
        return self._is_list_item(next_line_stripped)

    def _line_starts_unindented_children(
        self,
        stripped_line: str,
        indentation: int,
        is_list_item: bool,
        next_non_empty: tuple[str, int] | None,
    ) -> bool:
        stripped_without_bold = stripped_line.replace("**", "").strip()
        if not stripped_without_bold.endswith(":"):
            return False
        if next_non_empty is None:
            return False
        next_line_stripped, next_indentation = next_non_empty
        if not self._is_list_item(next_line_stripped):
            return False
        if is_list_item:
            return next_indentation <= indentation
        return True

    def _is_list_item(self, line: str) -> bool:
        return (
            _BULLET_ITEM_PATTERN.match(line) is not None
            or _NUMBERED_ITEM_PATTERN.match(line) is not None
        )

    def _find_next_non_empty_line(
        self, prepared_lines: list[tuple[str, int]], current_index: int
    ) -> tuple[str, int] | None:
        for future_index in range(current_index + 1, len(prepared_lines)):
            stripped_future_line, indentation = prepared_lines[future_index]
            if stripped_future_line:
                return stripped_future_line, indentation
        return None

    def _clean_title_text(self, raw_text: str) -> str:
        cleaned = raw_text.strip()
        if cleaned.endswith(":"):
            cleaned = cleaned[:-1].strip()
        if cleaned.startswith("**") and cleaned.endswith("**"):
            cleaned = cleaned[2:-2].strip()
        if cleaned.endswith(":"):
            cleaned = cleaned[:-1].strip()
        return cleaned

    def _clean_dangling_bold(self, text: str) -> str:
        cleaned = text.strip()
        if cleaned.count("**") % 2 == 1:
            last_index = cleaned.rfind("**")
            cleaned = cleaned[:last_index] + cleaned[last_index + 2 :]
            cleaned = " ".join(cleaned.split())
        return cleaned
