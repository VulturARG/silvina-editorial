from typing import Any
from unittest import TestCase
from unittest.mock import MagicMock

from src.domain.dtos.recommendation_dto import RecommendationDTO
from src.domain.dtos.recommendation_settings_dto import RecommendationSettingsDTO
from src.domain.enums.recommendation_priority import RecommendationPriority
from src.domain.recommendation.analysis_context import AnalysisContext
from src.domain.recommendation.dimension_rule import DimensionRule


def _create_analysis_context(
    dimension_scores: dict[str, dict[str, Any]],
    dimension_threshold: float = 6.0,
) -> AnalysisContext:
    return AnalysisContext(
        classification=MagicMock(),
        quality=MagicMock(dimension_scores=dimension_scores),
        structure=MagicMock(),
        citations=MagicMock(total_citations=0, matched_count=0),
        apa_validation=MagicMock(),
        grammar=MagicMock(),
        settings=RecommendationSettingsDTO(
            publish_threshold=7.0,
            quality_threshold=7.0,
            grammar_threshold=7.0,
            dimension_threshold=dimension_threshold,
            citation_match_threshold=90.0,
            critical_citation_match_threshold=50.0,
            citation_count_threshold=10,
            classification_confidence_threshold=0.7,
            critical_quality_threshold=5.0,
            critical_grammar_threshold=5.0,
        ),
    )


class TestDimensionRule(TestCase):
    def test_evaluates_low_score_dimension_to_medium_priority_recommendation(self):
        dimension_scores = {
            "coherencia": {
                "score": 4.5,
                "feedback": "La conexión lógica entre párrafos presenta deficiencias.",
            }
        }
        context = _create_analysis_context(dimension_scores=dimension_scores)
        rule = DimensionRule()

        recommendations = rule.evaluate(context)

        self.assertEqual(len(recommendations), 1)
        recommendation = recommendations[0]
        self.assertIsInstance(recommendation, RecommendationDTO)
        self.assertEqual(recommendation.priority, RecommendationPriority.MEDIUM)
        self.assertEqual(
            recommendation.message,
            'Dimensión "Coherencia" tiene puntuación baja (4.5). La conexión lógica entre párrafos presenta deficiencias.',
        )

    def test_dimension_with_score_above_threshold_produces_no_recommendations(self):
        dimension_scores = {
            "claridad": {
                "score": 8.0,
                "feedback": "El texto es muy claro.",
            }
        }
        context = _create_analysis_context(dimension_scores=dimension_scores)
        rule = DimensionRule()

        recommendations = rule.evaluate(context)

        self.assertEqual(recommendations, [])

    def test_markdown_bold_markers_removed_from_recommendation_message(self):
        dimension_scores = {
            "conclusiones": {
                "score": 4.0,
                "feedback": "El fragmento evidencia **argumentación académica rigurosa pero incompleta**.",
            }
        }
        context = _create_analysis_context(dimension_scores=dimension_scores)
        rule = DimensionRule()

        recommendations = rule.evaluate(context)

        self.assertEqual(len(recommendations), 1)
        self.assertNotIn("**", recommendations[0].message)
        self.assertEqual(
            recommendations[0].message,
            'Dimensión "Conclusiones" tiene puntuación baja (4.0). El fragmento evidencia argumentación académica rigurosa pero incompleta.',
        )

    def test_markdown_heading_markers_removed_from_recommendation_message(self):
        dimension_scores = {
            "conclusiones": {
                "score": 3.5,
                "feedback": "### Análisis del Cierre. ### **Síntesis Final** Se requiere mayor desarrollo.",
            }
        }
        context = _create_analysis_context(dimension_scores=dimension_scores)
        rule = DimensionRule()

        recommendations = rule.evaluate(context)

        self.assertEqual(len(recommendations), 1)
        self.assertNotIn("#", recommendations[0].message)
        self.assertNotIn("**", recommendations[0].message)
        self.assertEqual(
            recommendations[0].message,
            'Dimensión "Conclusiones" tiene puntuación baja (3.5). Análisis del Cierre. Síntesis Final Se requiere mayor desarrollo.',
        )

    def test_whitespace_is_collapsed_in_recommendation_message(self):
        dimension_scores = {
            "argumentacion": {
                "score": 4.0,
                "feedback": "   Primera línea.   \n\n   Segunda línea con   espacios múltiples.   ",
            }
        }
        context = _create_analysis_context(dimension_scores=dimension_scores)
        rule = DimensionRule()

        recommendations = rule.evaluate(context)

        self.assertEqual(len(recommendations), 1)
        self.assertEqual(
            recommendations[0].message,
            'Dimensión "Argumentación" tiene puntuación baja (4.0). Primera línea. Segunda línea con espacios múltiples.',
        )

    def test_markdown_single_asterisk_italic_markers_removed_from_recommendation_message(
        self,
    ) -> None:
        dimension_scores = {
            "argumentacion": {
                "score": 4.0,
                "feedback": "El texto no emplea *correctamente* el *mecanismo* del *cual* depende.",
            }
        }
        context = _create_analysis_context(dimension_scores=dimension_scores)
        rule = DimensionRule()

        recommendations = rule.evaluate(context)

        self.assertEqual(len(recommendations), 1)
        self.assertEqual(
            recommendations[0].message,
            'Dimensión "Argumentación" tiene puntuación baja (4.0). El texto no emplea correctamente el mecanismo del cual depende.',
        )

    def test_markdown_bold_and_italic_in_one_line_and_lone_asterisks_preserved(self) -> None:
        dimension_scores = {
            "claridad": {
                "score": 5.0,
                "feedback": "Revisar **negrita** y *cursiva*. Operación a * b, escala 1 x 10^11 y nota*.",
            }
        }
        context = _create_analysis_context(dimension_scores=dimension_scores)
        rule = DimensionRule()

        recommendations = rule.evaluate(context)

        self.assertEqual(len(recommendations), 1)
        self.assertEqual(
            recommendations[0].message,
            'Dimensión "Claridad" tiene puntuación baja (5.0). Revisar negrita y cursiva. Operación a * b, escala 1 x 10^11 y nota*.',
        )
