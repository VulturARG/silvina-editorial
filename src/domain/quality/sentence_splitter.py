from re import IGNORECASE, Match, compile

_CANDIDATE_BOUNDARY_PATTERN = compile(r"([.!?]+[\"'”’»\)\]\*]*)\s+(?=[A-ZÁÉÍÓÚÜÑ¿¡\"'“‘«\(\[\*])")
_KNOWN_ABBREVIATIONS_PATTERN = compile(
    r"\b(?:et\s+al|etc|ej|p|pp|vol|ed|dr|dra|sr|sra|fig|cf)$",
    IGNORECASE,
)
_SINGLE_LETTER_INITIAL_PATTERN = compile(r"\b[A-ZÁÉÍÓÚÜÑ]$")


class SentenceSplitter:
    """Splits and caps text into sentences preserving punctuation and formatting."""

    def split(self, text: str) -> list[str]:
        """Split text into sentences without breaking on abbreviations, initials, or numbers."""
        clean_text = text.strip()
        if not clean_text:
            return []

        boundaries = self._find_sentence_boundaries(clean_text)
        if not boundaries:
            return [clean_text]

        sentences: list[str] = []
        sentence_start_index = 0
        for boundary in boundaries:
            sentence = clean_text[sentence_start_index : boundary.end(1)].strip()
            if sentence:
                sentences.append(sentence)
            sentence_start_index = boundary.end()

        remaining_text = clean_text[sentence_start_index:].strip()
        if remaining_text:
            sentences.append(remaining_text)

        return sentences

    def cap_sentences(self, text: str, maximum_sentences: int = 3) -> str:
        """Cap text to a maximum sentence count preserving natural terminal punctuation."""
        clean_text = text.strip()
        if not clean_text or maximum_sentences <= 0:
            return ""

        boundaries = self._find_sentence_boundaries(clean_text)
        if len(boundaries) >= maximum_sentences:
            selected_boundary = boundaries[maximum_sentences - 1]
            return clean_text[: selected_boundary.end(1)].strip()

        return clean_text

    def _find_sentence_boundaries(self, text: str) -> list[Match[str]]:
        boundaries: list[Match[str]] = []
        for candidate_match in _CANDIDATE_BOUNDARY_PATTERN.finditer(text):
            punctuation_with_delimiters = candidate_match.group(1)
            if "." in punctuation_with_delimiters:
                period_index = candidate_match.start(1) + punctuation_with_delimiters.rfind(".")
                preceding_text = text[:period_index].rstrip()
                following_text = text[period_index + 1 :]
                is_inside_number = bool(
                    preceding_text
                    and preceding_text[-1].isdigit()
                    and following_text
                    and following_text[0].isdigit()
                )
                if is_inside_number:
                    continue
                if _SINGLE_LETTER_INITIAL_PATTERN.search(preceding_text) is not None:
                    continue
                if _KNOWN_ABBREVIATIONS_PATTERN.search(preceding_text) is not None:
                    continue
            boundaries.append(candidate_match)
        return boundaries
