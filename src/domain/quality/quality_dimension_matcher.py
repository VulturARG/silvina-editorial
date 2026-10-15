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
    first 200 characters of the block header line are inspected, so a keyword in
    the section body never changes the dimension named by its header.
    """

    def match(self, block: str) -> QualityDimension | None:
        """Match a text block to a quality dimension using keyword heuristics."""
        header_line = block.strip().split("\n", 1)[0]
        header_lower = header_line[:_CHARACTER_INSPECTION_LIMIT].lower()
        for dimension, keywords in _DIMENSION_KEYWORDS:
            if any(keyword in header_lower for keyword in keywords):
                return dimension
        return None
