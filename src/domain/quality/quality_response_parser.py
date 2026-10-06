from re import IGNORECASE, compile

from src.domain.dtos.dimension_score_dto import DimensionScoreDTO
from src.domain.dtos.feedback_block_dto import FeedbackBlockDTO
from src.domain.dtos.parsed_response_dto import ParsedResponseDTO
from src.domain.enums.quality_dimension import QualityDimension
from src.domain.quality.dimension_feedback_extractor import DimensionFeedbackExtractor
from src.domain.quality.dimension_score_extractor import DimensionScoreExtractor
from src.domain.quality.quality_dimension_matcher import QualityDimensionMatcher

_DIMENSION_HEADER_PATTERN = compile(
    r"(?m)(?=^[ \t]*(?:#{1,6}[ \t]+)?\*\*(?:\d+\.\s*)?(?:Claridad|Coherencia|Argumentaci[oó]n|Conclusiones))",
    IGNORECASE,
)


class QualityResponseParser:
    """Parses LLM response text into structured per-dimension scores and feedback."""

    def __init__(
        self,
        dimension_matcher: QualityDimensionMatcher,
        score_extractor: DimensionScoreExtractor,
        feedback_extractor: DimensionFeedbackExtractor,
        unscored_dimension: DimensionScoreDTO,
    ) -> None:
        self._dimension_matcher = dimension_matcher
        self._score_extractor = score_extractor
        self._feedback_extractor = feedback_extractor
        self._unscored_dimension = unscored_dimension

    def parse(self, text: str) -> ParsedResponseDTO:
        """Parse an LLM response into a ParsedResponseDTO of per-dimension scores."""
        matched_scores: dict[QualityDimension, DimensionScoreDTO] = {}

        blocks = _DIMENSION_HEADER_PATTERN.split(text.strip())
        for block in blocks:
            if not block.strip():
                continue

            dimension = self._dimension_matcher.match(block)
            if dimension is None:
                continue

            feedback_result = self._feedback_extractor.extract(block)
            existing_score = matched_scores.get(dimension)
            if self._should_ignore_candidate(existing_score, feedback_result.blocks):
                continue

            score = self._score_extractor.extract(block)
            matched_scores[dimension] = DimensionScoreDTO(
                score=score,
                feedback=feedback_result.feedback,
                feedback_blocks=feedback_result.blocks,
            )

        scores = {
            dimension: matched_scores.get(dimension, self._unscored_dimension)
            for dimension in QualityDimension
        }
        return ParsedResponseDTO(
            scores=scores,
            matched_dimensions=frozenset(matched_scores.keys()),
        )

    def _should_ignore_candidate(
        self,
        existing_score: DimensionScoreDTO | None,
        candidate_blocks: tuple[FeedbackBlockDTO, ...],
    ) -> bool:
        return (
            existing_score is not None
            and bool(existing_score.feedback_blocks)
            and not candidate_blocks
        )
