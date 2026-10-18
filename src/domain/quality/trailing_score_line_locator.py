from re import IGNORECASE, compile

from src.domain.dtos.trailing_score_dto import TrailingScoreDTO

_MINIMUM_SCORE = 0.0
_MAXIMUM_SCORE = 10.0

_HEADER_EXPLICIT_SCORE_PATTERN = compile(
    r"Puntuaci[oó]n:\s*\d|\d+(?:\.\d+)?\s*/\s*10",
    IGNORECASE,
)
_TRAILING_SCORE_LINE_PATTERN = compile(
    r"(?:\[|\*\*)*\s*Puntuaci[oó]n:\s*(\d+(?:\.\d+)?)(?:\s*/\s*10)?\s*(?:\]|\*\*)*\.?",
    IGNORECASE,
)


class TrailingScoreLineLocator:
    """Locates a dimension block whose score is written on its last line, after the analysis."""

    def locate(self, block: str) -> TrailingScoreDTO | None:
        """Return the trailing score and the block without its line, or None outside the score-last layout."""
        lines = block.split("\n")
        if _HEADER_EXPLICIT_SCORE_PATTERN.search(lines[0]) is not None:
            return None

        non_empty_line_indexes = [index for index, line in enumerate(lines) if line.strip()]
        if not non_empty_line_indexes:
            return None

        last_line_index = non_empty_line_indexes[-1]
        score_match = _TRAILING_SCORE_LINE_PATTERN.fullmatch(lines[last_line_index].strip())
        if score_match is None:
            return None

        return TrailingScoreDTO(
            score=self._clamp(float(score_match.group(1))),
            block_without_score_line="\n".join(lines[:last_line_index]),
        )

    def _clamp(self, score: float) -> float:
        return max(_MINIMUM_SCORE, min(_MAXIMUM_SCORE, score))
