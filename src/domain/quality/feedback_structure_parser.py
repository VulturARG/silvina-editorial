from re import compile

from src.domain.dtos.feedback_block_dto import FeedbackBlockDTO
from src.domain.enums.feedback_block_kind import FeedbackBlockKind

_HORIZONTAL_RULE_PATTERN = compile(r"^(?:(?:-[ \t]*){3,}|(?:\*[ \t]*){3,}|(?:_[ \t]*){3,})$")
_BLOCKQUOTE_MARKER_PATTERN = compile(r"^[ \t]*>[ \t]*")
_HEADING_LINE_PATTERN = compile(r"^(#{1,6})\s+(.*)$")
_BOLD_TITLE_LINE_PATTERN = compile(r"^\*\*([^*]+)\*\*:?$")
_BULLET_ITEM_PATTERN = compile(r"^([-*+])[ \t]+(.*)$")
_NUMBERED_ITEM_PATTERN = compile(r"^(\d+)\.[ \t]+(.*)$")


class FeedbackStructureParser:
    """Parses raw dimension feedback lines into a sequence of structured blocks."""

    def __init__(self, maximum_items_per_section: int = 3) -> None:
        self._maximum_items_per_section = maximum_items_per_section

    def parse(
        self, lines: list[str], dimension_heading_level: int = 0
    ) -> tuple[FeedbackBlockDTO, ...]:
        """Parse dimension lines into capped structured feedback blocks."""
        sections: list[tuple[FeedbackBlockDTO | None, list[FeedbackBlockDTO]]] = []
        current_title: FeedbackBlockDTO | None = None
        current_blocks: list[FeedbackBlockDTO] = []
        previous_top_level_indentation: int | None = None

        for raw_line in lines:
            line_without_blockquote = _BLOCKQUOTE_MARKER_PATTERN.sub("", raw_line)
            stripped_line = line_without_blockquote.strip()

            if not stripped_line:
                continue

            if _HORIZONTAL_RULE_PATTERN.match(stripped_line) is not None:
                break

            if stripped_line.startswith("|"):
                continue

            heading_match = _HEADING_LINE_PATTERN.match(stripped_line)
            if heading_match is not None:
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

            indentation = len(line_without_blockquote) - len(line_without_blockquote.lstrip())

            bullet_match = _BULLET_ITEM_PATTERN.match(stripped_line)
            if bullet_match is not None:
                content = self._clean_dangling_bold(bullet_match.group(2))
                if not content:
                    continue
                if (
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
                continue

            numbered_match = _NUMBERED_ITEM_PATTERN.match(stripped_line)
            if numbered_match is not None:
                content = self._clean_dangling_bold(numbered_match.group(2))
                if not content:
                    continue
                if (
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
            current_parent_kept = False

            for block in blocks:
                if block.level == 0:
                    if top_level_count < self._maximum_items_per_section:
                        kept_blocks.append(block)
                        top_level_count += 1
                        current_parent_kept = True
                    else:
                        current_parent_kept = False
                else:
                    if current_parent_kept:
                        kept_blocks.append(block)

            if title is not None:
                if kept_blocks:
                    result_blocks.append(title)
                    result_blocks.extend(kept_blocks)
            else:
                result_blocks.extend(kept_blocks)

        return tuple(result_blocks)

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
