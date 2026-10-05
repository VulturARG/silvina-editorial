from src.domain.dtos.apa_validation_result_dto import ApaValidationResultDTO
from src.domain.dtos.citation_analysis_result_dto import CitationAnalysisResultDTO
from src.domain.dtos.classification_result_dto import ClassificationResultDTO
from src.domain.dtos.grammar_check_result_dto import GrammarCheckResultDTO
from src.domain.dtos.publication_verdict_dto import PublicationVerdictDTO
from src.domain.dtos.quality_result_dto import QualityResultDTO
from src.domain.dtos.recommendation_dto import RecommendationDTO
from src.domain.dtos.recommendation_settings_dto import RecommendationSettingsDTO
from src.domain.dtos.structure_validation_result_dto import StructureValidationResultDTO
from src.domain.recommendation.analysis_context import AnalysisContext
from src.domain.recommendation.citation_count_rule import CitationCountRule
from src.domain.recommendation.citation_match_rule import CitationMatchRule
from src.domain.recommendation.confidence_rule import ConfidenceRule
from src.domain.recommendation.dimension_rule import DimensionRule
from src.domain.recommendation.grammar_rule import GrammarRule
from src.domain.recommendation.publication_verdict_evaluator import PublicationVerdictEvaluator
from src.domain.recommendation.quality_rule import QualityRule
from src.domain.recommendation.recommendation_rule import RecommendationRule
from src.domain.recommendation.structure_rule import StructureRule

_DEFAULT_RULES: list[RecommendationRule] = [
    QualityRule(),
    GrammarRule(),
    DimensionRule(),
    StructureRule(),
    CitationMatchRule(),
    CitationCountRule(),
    ConfidenceRule(),
]


class RecommendationBuilder:
    """Domain service for generating editorial recommendations and publication verdict."""

    def __init__(
        self,
        recommendation_settings: RecommendationSettingsDTO,
        rules: list[RecommendationRule] | None = None,
        verdict_evaluator: PublicationVerdictEvaluator | None = None,
    ) -> None:
        self._recommendation_settings = recommendation_settings
        self._rules = rules if rules is not None else _DEFAULT_RULES
        self._verdict_evaluator = verdict_evaluator or PublicationVerdictEvaluator()

    def build(
        self,
        classification: ClassificationResultDTO,
        quality: QualityResultDTO,
        structure: StructureValidationResultDTO,
        citations: CitationAnalysisResultDTO,
        apa_validation: ApaValidationResultDTO,
        grammar: GrammarCheckResultDTO,
    ) -> tuple[list[RecommendationDTO], PublicationVerdictDTO]:
        """Evaluate analysis results and return specific recommendations plus the publication verdict."""
        context = AnalysisContext(
            classification=classification,
            quality=quality,
            structure=structure,
            citations=citations,
            apa_validation=apa_validation,
            grammar=grammar,
            settings=self._recommendation_settings,
        )
        recommendations: list[RecommendationDTO] = []
        for rule in self._rules:
            recommendations.extend(rule.evaluate(context))
        verdict = self._verdict_evaluator.evaluate(context)
        return recommendations, verdict
