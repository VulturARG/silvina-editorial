from re import IGNORECASE, compile

from src.domain.dtos.dimension_score_dto import DimensionScoreDTO

_MINIMUM_SCORE = 0.0
_MAXIMUM_SCORE = 10.0

_EXPLICIT_SCORE_PATTERN = compile(
    r"\[Puntuaci[oó]n:\s*(\d+(?:\.\d+)?)(?:/10)?\]|(\d+(?:\.\d+)?)\s*/\s*10",
    IGNORECASE,
)
_NARRATIVE_SCORE_KEYWORDS: tuple[tuple[tuple[str, ...], float], ...] = (
    (("excelente", "sobresaliente", "muy bueno"), 8.5),
    (("bueno", "adecuado", "correcto"), 7.5),
    (("aceptable", "suficiente", "regular"), 6.0),
    (("deficiente", "débil", "pobre", "insuficiente"), 4.0),
)


class DimensionScoreExtractor:
    """Extracts numerical scores from text blocks via explicit score markers or narrative inference."""

    def __init__(self, unscored_dimension: DimensionScoreDTO) -> None:
        self._unscored_dimension = unscored_dimension

    def extract(self, block: str) -> float:
        """Extract a clamped score from explicit score notation or inferred narrative keywords."""
        match = _EXPLICIT_SCORE_PATTERN.search(block)
        if match is not None:
            score_text = match.group(1) or match.group(2)
            return max(_MINIMUM_SCORE, min(_MAXIMUM_SCORE, float(score_text)))

        return self._infer_score_from_narrative(block)

    def _infer_score_from_narrative(self, block: str) -> float:
        block_lower = block.lower()
        for keywords, score in _NARRATIVE_SCORE_KEYWORDS:
            if any(keyword in block_lower for keyword in keywords):
                return score
        return self._unscored_dimension.score
