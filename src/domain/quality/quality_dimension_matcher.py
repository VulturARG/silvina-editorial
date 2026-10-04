from src.domain.enums.quality_dimension import QualityDimension

_CHARACTER_INSPECTION_LIMIT = 200

_DIMENSION_KEYWORDS: tuple[tuple[QualityDimension, tuple[str, ...]], ...] = (
    (QualityDimension.ARGUMENTATION, ("argumentaci",)),
    (QualityDimension.CONCLUSIONS, ("conclusi",)),
    (QualityDimension.COHERENCE, ("coherencia",)),
    (QualityDimension.CLARITY, ("claridad", "argumento")),
)


class QualityDimensionMatcher:
    """Matches text blocks to QualityDimension based on an ordered keyword table.

    Evaluation order is significant: ARGUMENTATION (matching 'argumentaci') and
    CONCLUSIONS (matching 'conclusi') are evaluated before COHERENCE and CLARITY.
    In particular, 'argumento' resolves to CLARITY, not ARGUMENTATION. Only the
    first 200 characters of the block are inspected.
    """

    def match(self, block: str) -> QualityDimension | None:
        """Match a text block to a quality dimension using keyword heuristics."""
        block_lower = block[:_CHARACTER_INSPECTION_LIMIT].lower()
        for dimension, keywords in _DIMENSION_KEYWORDS:
            if any(keyword in block_lower for keyword in keywords):
                return dimension
        return None
