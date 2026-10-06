from src.domain.quality.first_sentence_extractor import FirstSentenceExtractor


class SuitabilityFieldTruncator:
    """Truncates field text at sentence and word boundaries according to length limits."""

    def __init__(self, first_sentence_extractor: FirstSentenceExtractor) -> None:
        self._first_sentence_extractor = first_sentence_extractor

    def truncate(self, raw_text: str, max_length: int) -> str:
        """Truncate raw text to first sentence and word boundary if exceeding max length."""
        if not raw_text:
            return raw_text
        sentence = self._first_sentence_extractor.extract_first_sentence(raw_text)
        if len(sentence) < max_length:
            return sentence
        return self._truncate_to_word_boundary(sentence, max_length)

    def _truncate_to_word_boundary(self, text: str, max_length: int) -> str:
        limit = max_length - 2
        truncated = text[:limit]
        last_space = truncated.rfind(" ")
        if last_space > 0:
            truncated = truncated[:last_space]
        return f"{truncated.rstrip(' .,;:')}…"
