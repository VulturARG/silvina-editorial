from re import IGNORECASE, compile as re_compile

from src.domain.quality.suitability_field_extractor import SuitabilityFieldExtractor

_LINES_LABEL_PATTERN = re_compile(r"(?:\*\*)?L[IÍ]NEAS\s*(?:\*\*)?\s*:", IGNORECASE)
_NEXT_LABEL_PATTERN = re_compile(r"(?:\*\*)?[A-ZÁÉÍÓÚ]+\s*(?:\*\*)?\s*:", IGNORECASE)
_LIST_MARKER_PATTERN = re_compile(r"^[ \t]*(?:[-*+]|\d+\.)[ \t]+(.*)")


class AlignmentLinesExtractor:
    """Extracts research lines from alignment evaluation text."""

    def __init__(self, field_extractor: SuitabilityFieldExtractor) -> None:
        self._field_extractor = field_extractor

    def extract(self, text: str) -> str:
        """Extract alignment lines value from text."""
        same_line_value = self._field_extractor.extract_lines_same_line(text)
        if same_line_value:
            return same_line_value

        label_match = _LINES_LABEL_PATTERN.search(text)
        if not label_match:
            return ""

        remaining_text = text[label_match.end() :]
        first_line, _, subsequent_lines = remaining_text.partition("\n")
        cleaned_first_line = self._field_extractor.clean_value(first_line)
        if cleaned_first_line:
            return cleaned_first_line

        return self._extract_list_items(subsequent_lines)

    def _extract_list_items(self, text: str) -> str:
        list_items: list[str] = []
        for raw_line in text.split("\n"):
            stripped_line = raw_line.strip()
            if not stripped_line:
                if list_items:
                    break
                continue
            item_content = self._parse_list_item(stripped_line)
            if item_content is None:
                break
            if item_content:
                list_items.append(item_content)
        return "; ".join(list_items)

    def _parse_list_item(self, line: str) -> str | None:
        if self._is_next_label(line):
            return None
        match = _LIST_MARKER_PATTERN.match(line)
        if not match:
            return None
        return match.group(1).replace("**", "").strip()

    def _is_next_label(self, line: str) -> bool:
        return bool(_NEXT_LABEL_PATTERN.match(line))
