from re import IGNORECASE, MULTILINE, Pattern, compile as re_compile

from src.domain.enums.editorial_alignment_verdict import EditorialAlignmentVerdict

_VERDICT_PATTERN = re_compile(r"VEREDICTO:\s*(.+)", IGNORECASE)
_CONTRIBUTION_PATTERN = re_compile(r"CONTRIBUCI[OÓ]N:\s*(.+)", IGNORECASE)
_LINES_PATTERN = re_compile(r"L[IÍ]NEAS:\s*(.+)", IGNORECASE)
_JUSTIFICATION_PATTERN = re_compile(r"JUSTIFICACI[OÓ]N:\s*(.+)", IGNORECASE)
_SENTENCE_END_PATTERN = re_compile(r"[.!?]")
_RESEARCH_LINE_PATTERN = re_compile(r"^(\d+)\.\s*([^—\n]+?)\s*(?:—.*)?$", MULTILINE)

_CONTRIBUTION_VERDICTS = ("NO SUSTENTADA", "PARCIAL", "SUSTENTADA")
_ALIGNMENT_VERDICTS = (
    EditorialAlignmentVerdict.NOT_ALIGNED.value,
    EditorialAlignmentVerdict.PARTIALLY_ALIGNED.value,
    EditorialAlignmentVerdict.ALIGNED.value,
)

_PHRASE_MAX_LENGTH = 120
_OBSERVATION_MAX_LENGTH = 120
_JUSTIFICATION_MAX_LENGTH = 120
_LINES_MAX_LENGTH = 80

_NOT_SUSTAINED_OBSERVATION = "Sin contribución observada o declarada."
_PARTIAL_OBSERVATION = "Contribución declarada pero no suficientemente sustentada."
_SUSTAINED_OBSERVATION_FALLBACK = "Contribución sustentada."


class EditorialSuitabilityParser:
    """Stateless parser that extracts verdicts and justifications from raw LLM text."""

    def parse_contribution(self, text: str) -> tuple[str, str, str]:
        """Return (contribution_verdict, contribution_phrase, contribution_observation)."""
        verdict = self._extract_verdict(text, _CONTRIBUTION_VERDICTS)
        phrase = self._truncate_field(
            self._extract_field(text, _CONTRIBUTION_PATTERN), _PHRASE_MAX_LENGTH
        )
        observation = self.build_contribution_observation(verdict, phrase)
        return verdict, phrase, observation

    def parse_alignment(self, text: str) -> tuple[str, str, str]:
        """Return (alignment_verdict, alignment_lines, alignment_justification)."""
        verdict = self._extract_verdict(text, _ALIGNMENT_VERDICTS)
        lines = self._truncate_field(self._extract_field(text, _LINES_PATTERN), _LINES_MAX_LENGTH)
        justification = self._truncate_field(
            self._extract_field(text, _JUSTIFICATION_PATTERN), _JUSTIFICATION_MAX_LENGTH
        )
        return verdict, lines, justification

    def build_contribution_observation(self, verdict: str, phrase: str) -> str:
        """Return the fixed observation text for a contribution verdict and its phrase."""
        if verdict == "NO SUSTENTADA":
            return _NOT_SUSTAINED_OBSERVATION
        if verdict == "PARCIAL":
            return _PARTIAL_OBSERVATION
        if not phrase:
            return _SUSTAINED_OBSERVATION_FALLBACK
        return self._truncate_field(f"Contribución sustentada — {phrase}", _OBSERVATION_MAX_LENGTH)

    def resolve_research_line_title(self, research_lines: str, line_id: str) -> str:
        """Return formatted 'ID. Title' extracted from research lines text, or line_id on miss."""
        for match in _RESEARCH_LINE_PATTERN.finditer(research_lines):
            if match.group(1) == line_id:
                return f"{match.group(1)}. {match.group(2).strip()}"
        return line_id

    def _extract_verdict(self, text: str, candidates: tuple[str, ...]) -> str:
        match = _VERDICT_PATTERN.search(text)
        raw = match.group(1).upper() if match else ""
        for candidate in candidates:
            if candidate in raw:
                return candidate
        return candidates[0]

    def _extract_field(self, text: str, pattern: Pattern) -> str:
        match = pattern.search(text)
        return match.group(1).strip() if match else ""

    def _truncate_field(self, raw: str, max_length: int) -> str:
        if not raw:
            return raw
        sentence = self._extract_first_sentence(raw)
        if len(sentence) < max_length:
            return sentence
        return self._truncate_to_word_boundary(sentence, max_length)

    def _extract_first_sentence(self, text: str) -> str:
        match = _SENTENCE_END_PATTERN.search(text)
        if match:
            return text[: match.start() + 1].strip()
        return text.strip()

    def _truncate_to_word_boundary(self, text: str, max_length: int) -> str:
        limit = max_length - 2
        truncated = text[:limit]
        last_space = truncated.rfind(" ")
        if last_space > 0:
            truncated = truncated[:last_space]
        return f"{truncated.rstrip(' .,;:')}…"
