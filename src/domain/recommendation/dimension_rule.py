from re import compile

from src.domain.dtos.recommendation_dto import RecommendationDTO
from src.domain.enums.quality_dimension import QualityDimension
from src.domain.enums.recommendation_priority import RecommendationPriority
from src.domain.recommendation.analysis_context import AnalysisContext
from src.domain.recommendation.recommendation_rule import RecommendationRule

_MARKDOWN_HEADING_PATTERN = compile(r"(?:^|(?<=\s))#{1,6}\s+")
_MARKDOWN_ITALIC_PATTERN = compile(r"(?<!\*)\*(?!\s|\*)([^\r\n*]+?)(?<!\s)\*(?!\*)")


class DimensionRule(RecommendationRule):
    """Generates recommendations for quality dimensions below threshold."""

    def evaluate(self, context: AnalysisContext) -> list[RecommendationDTO]:
        """Evaluate quality dimension scores and return recommendations for low scores."""
        recommendations: list[RecommendationDTO] = []
        for dimension_name, dimension_data in context.quality.dimension_scores.items():
            score = dimension_data["score"]
            if score < context.settings.dimension_threshold:
                feedback = self._clean_feedback(dimension_data.get("feedback", ""))
                dimension_label = QualityDimension.label_for(dimension_name)
                recommendations.append(
                    RecommendationDTO(
                        priority=RecommendationPriority.MEDIUM,
                        message=f'Dimensión "{dimension_label}" tiene puntuación baja ({score:.1f}). {feedback}',
                    )
                )
        return recommendations

    def _clean_feedback(self, feedback: str) -> str:
        cleaned_feedback = feedback.replace("**", "")
        cleaned_feedback = _MARKDOWN_ITALIC_PATTERN.sub(r"\1", cleaned_feedback)
        cleaned_feedback = _MARKDOWN_HEADING_PATTERN.sub("", cleaned_feedback)
        return " ".join(cleaned_feedback.split())
