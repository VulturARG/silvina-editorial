from src.domain.quality.feedback_structure_parser import FeedbackStructureParser
from src.domain.quality.quality_response_parser import QualityResponseParser
from src.domain.tests.quality.feedback_structure_parser_builder_for_test import (
    FeedbackStructureParserBuilderForTest,
)


class QualityResponseParserBuilderForTest:
    def build(
        self,
        unscored_dimension_score: float = 7.0,
        unscored_dimension_feedback: str = "No disponible",
        feedback_structure_parser: FeedbackStructureParser | None = None,
        maximum_items_per_section: int = 8,
    ) -> QualityResponseParser:
        structure_parser = (
            feedback_structure_parser
            if feedback_structure_parser is not None
            else FeedbackStructureParserBuilderForTest().build(
                maximum_items_per_section=maximum_items_per_section
            )
        )
        return QualityResponseParser(
            feedback_structure_parser=structure_parser,
            unscored_dimension_score=unscored_dimension_score,
            unscored_dimension_feedback=unscored_dimension_feedback,
        )
