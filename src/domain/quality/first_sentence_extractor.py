from re import compile as re_compile

_SENTENCE_END_PATTERN = re_compile(r"[.!?]")
_LIST_NUMBER_PREFIX_PATTERN = re_compile(r"(?:^|[\r\n]|[;,(\[]|(?<!\d)[:\-])[ \t]*(?<!\d)\d{1,2}$")


class FirstSentenceExtractor:
    """Extracts the first sentence of a text while preserving list numbers and decimals."""

    def extract_first_sentence(self, text: str) -> str:
        """Return the first sentence of the text based on punctuation rules."""
        for match in _SENTENCE_END_PATTERN.finditer(text):
            punctuation = match.group()
            if punctuation in ("!", "?"):
                return text[: match.end()].strip()

            index = match.start()
            if self._is_period_between_digits(text, index):
                continue
            if self._is_list_number_period(text, index):
                continue

            return text[: match.end()].strip()

        return text.strip()

    def _is_period_between_digits(self, text: str, index: int) -> bool:
        return (
            index > 0
            and index + 1 < len(text)
            and text[index - 1].isdigit()
            and text[index + 1].isdigit()
        )

    def _is_list_number_period(self, text: str, index: int) -> bool:
        return bool(_LIST_NUMBER_PREFIX_PATTERN.search(text[:index]))
