from re import IGNORECASE, Pattern, compile as re_compile

_FIELD_PATTERN_TEMPLATE = r"(?:\*\*)?{label}\s*(?:\*\*)?\s*:[*\s:]*([^*:\s].*)"

_VERDICT_PATTERN = re_compile(_FIELD_PATTERN_TEMPLATE.format(label="VEREDICTO"), IGNORECASE)
_CONTRIBUTION_PATTERN = re_compile(
    _FIELD_PATTERN_TEMPLATE.format(label=r"CONTRIBUCI[OÓ]N"), IGNORECASE
)
_JUSTIFICATION_PATTERN = re_compile(
    _FIELD_PATTERN_TEMPLATE.format(label=r"JUSTIFICACI[OÓ]N"), IGNORECASE
)
_LINES_SAME_LINE_PATTERN = re_compile(
    r"(?:\*\*)?L[IÍ]NEAS\s*(?:\*\*)?\s*:[* \t:]*([^*\s\r\n].*)", IGNORECASE
)


class SuitabilityFieldExtractor:
    """Extracts raw suitability fields and verdict text using standardized patterns."""

    def clean_value(self, raw_value: str) -> str:
        """Strip markdown markers and leading punctuation from a field value."""
        return raw_value.replace("**", "").lstrip("* :").strip()

    def extract_verdict_text(self, text: str) -> str:
        """Extract raw uppercase verdict text from text."""
        cleaned_value = self._extract_matched_value(text, _VERDICT_PATTERN)
        return cleaned_value.upper()

    def extract_contribution_phrase(self, text: str) -> str:
        """Extract raw contribution phrase from text."""
        return self._extract_matched_value(text, _CONTRIBUTION_PATTERN)

    def extract_justification(self, text: str) -> str:
        """Extract raw justification from text."""
        return self._extract_matched_value(text, _JUSTIFICATION_PATTERN)

    def extract_lines_same_line(self, text: str) -> str:
        """Extract lines value when present on the same line as the label."""
        return self._extract_matched_value(text, _LINES_SAME_LINE_PATTERN)

    def _extract_matched_value(self, text: str, pattern: Pattern[str]) -> str:
        match = pattern.search(text)
        if not match:
            return ""
        return self.clean_value(match.group(1))
