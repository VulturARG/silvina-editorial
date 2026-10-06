from src.domain.dtos.dimension_score_dto import DimensionScoreDTO
from src.domain.quality.dimension_feedback_extractor import DimensionFeedbackExtractor
from src.domain.quality.dimension_score_extractor import DimensionScoreExtractor
from src.domain.quality.feedback_structure_parser import FeedbackStructureParser
from src.domain.quality.quality_dimension_matcher import QualityDimensionMatcher
from src.domain.quality.quality_response_parser import QualityResponseParser
from src.domain.tests.quality.feedback_structure_parser_builder_for_test import (
    FeedbackStructureParserBuilderForTest,
)


class QualityResponseParserBuilderForTest:
    """Builds QualityResponseParser instances with configurable test defaults."""

    def build(
        self,
        unscored_dimension_score: float = 7.0,
        unscored_dimension_feedback: str = "No disponible",
        feedback_structure_parser: FeedbackStructureParser | None = None,
        maximum_items_per_section: int = 8,
        dimension_matcher: QualityDimensionMatcher | None = None,
        score_extractor: DimensionScoreExtractor | None = None,
        feedback_extractor: DimensionFeedbackExtractor | None = None,
    ) -> QualityResponseParser:
        structure_parser = (
            feedback_structure_parser
            if feedback_structure_parser is not None
            else FeedbackStructureParserBuilderForTest().build(
                maximum_items_per_section=maximum_items_per_section
            )
        )
        unscored_dimension = DimensionScoreDTO(
            score=unscored_dimension_score,
            feedback=unscored_dimension_feedback,
            feedback_blocks=(),
        )
        resolved_dimension_matcher = (
            dimension_matcher if dimension_matcher is not None else QualityDimensionMatcher()
        )
        resolved_score_extractor = (
            score_extractor
            if score_extractor is not None
            else DimensionScoreExtractor(unscored_dimension=unscored_dimension)
        )
        resolved_feedback_extractor = (
            feedback_extractor
            if feedback_extractor is not None
            else DimensionFeedbackExtractor(
                feedback_structure_parser=structure_parser,
                unscored_dimension=unscored_dimension,
            )
        )
        return QualityResponseParser(
            dimension_matcher=resolved_dimension_matcher,
            score_extractor=resolved_score_extractor,
            feedback_extractor=resolved_feedback_extractor,
            unscored_dimension=unscored_dimension,
        )
