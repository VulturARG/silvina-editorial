from unittest import TestCase

from src.domain.classification.classification_rule_table import ClassificationRuleTable
from src.domain.dtos.classification_signals_dto import ClassificationSignalsDTO
from src.domain.enums.article_type import ArticleType


class TestClassificationRuleTablePopularScienceNearMiss(TestCase):
    def setUp(self) -> None:
        self._rule_table = ClassificationRuleTable()

    def test_case_6_full_core_with_theoretical_justification_only(self) -> None:
        signals = self._build_signals(
            has_sufficient_reference_count=False,
            has_recent_references=False,
            has_methodological_vocabulary=True,
            has_research_intent=True,
            has_evidence_based_contribution=True,
            has_theoretical_justification=True,
        )

        matched_rule = self._rule_table.evaluate(signals)

        self.assertEqual(matched_rule.article_type, ArticleType.POPULAR_SCIENCE)
        self.assertIsNone(matched_rule.confidence)
        self.assertIn(
            "carece del respaldo bibliográfico mínimo requerido",
            matched_rule.reasoning_template,
        )

    def test_case_7_full_core_with_recent_references_only(self) -> None:
        signals = self._build_signals(
            has_sufficient_reference_count=False,
            has_recent_references=True,
            has_methodological_vocabulary=True,
            has_research_intent=True,
            has_evidence_based_contribution=True,
            has_theoretical_justification=False,
        )

        matched_rule = self._rule_table.evaluate(signals)

        self.assertEqual(matched_rule.article_type, ArticleType.POPULAR_SCIENCE)
        self.assertIsNone(matched_rule.confidence)
        self.assertIn("con bibliografía reciente (S2b)", matched_rule.reasoning_template)

    def test_case_8_full_core_with_reference_count_only(self) -> None:
        signals = self._build_signals(
            has_sufficient_reference_count=True,
            has_recent_references=False,
            has_methodological_vocabulary=True,
            has_research_intent=True,
            has_evidence_based_contribution=True,
            has_theoretical_justification=False,
        )

        matched_rule = self._rule_table.evaluate(signals)

        self.assertEqual(matched_rule.article_type, ArticleType.POPULAR_SCIENCE)
        self.assertIsNone(matched_rule.confidence)
        self.assertIn(
            "con cantidad de referencias suficiente (S2a)", matched_rule.reasoning_template
        )

    def test_case_9_near_miss_with_zero_structural_support_yields_popular_science(self) -> None:
        signals = self._build_signals(
            has_sufficient_reference_count=False,
            has_recent_references=False,
            has_methodological_vocabulary=True,
            has_research_intent=True,
            has_evidence_based_contribution=True,
            has_theoretical_justification=False,
        )

        matched_rule = self._rule_table.evaluate(signals)

        self.assertEqual(matched_rule.article_type, ArticleType.POPULAR_SCIENCE)
        self.assertIsNone(matched_rule.confidence)
        self.assertIn(
            "Las señales cualitativas sin soporte estructural son insuficientes",
            matched_rule.reasoning_template,
        )

    def _build_signals(self, **kwargs: bool) -> ClassificationSignalsDTO:
        return ClassificationSignalsDTO(**kwargs)
