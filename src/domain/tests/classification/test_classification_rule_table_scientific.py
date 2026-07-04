from unittest import TestCase

from src.domain.classification.classification_rule_table import ClassificationRuleTable
from src.domain.dtos.classification_signals_dto import ClassificationSignalsDTO
from src.domain.enums.article_type import ArticleType


class TestClassificationRuleTableScientific(TestCase):
    def setUp(self) -> None:
        self._rule_table = ClassificationRuleTable()

    def test_case_2_full_signal_set_produces_zero_point_nine_confidence(self) -> None:
        signals = self._build_signals(
            has_sufficient_reference_count=True,
            has_recent_references=True,
            has_methodological_vocabulary=True,
            has_research_intent=True,
            has_evidence_based_contribution=True,
            has_theoretical_justification=True,
        )

        matched_rule = self._rule_table.evaluate(signals)

        self.assertEqual(matched_rule.article_type, ArticleType.SCIENTIFIC)
        self.assertEqual(matched_rule.confidence, 0.90)
        self.assertIn(
            "Artículo científico con muy elevada confianza.",
            matched_rule.reasoning_template,
        )

    def test_case_3_missing_s2a_produces_zero_point_eight_six_confidence(self) -> None:
        signals = self._build_signals(
            has_sufficient_reference_count=False,
            has_recent_references=True,
            has_methodological_vocabulary=True,
            has_research_intent=True,
            has_evidence_based_contribution=True,
            has_theoretical_justification=True,
        )

        matched_rule = self._rule_table.evaluate(signals)

        self.assertEqual(matched_rule.article_type, ArticleType.SCIENTIFIC)
        self.assertEqual(matched_rule.confidence, 0.86)
        self.assertIn(
            "Artículo científico con confianza elevada.",
            matched_rule.reasoning_template,
        )

    def test_case_4_missing_s6_produces_zero_point_eight_five_confidence(self) -> None:
        signals = self._build_signals(
            has_sufficient_reference_count=True,
            has_recent_references=True,
            has_methodological_vocabulary=True,
            has_research_intent=True,
            has_evidence_based_contribution=True,
            has_theoretical_justification=False,
        )

        matched_rule = self._rule_table.evaluate(signals)

        self.assertEqual(matched_rule.article_type, ArticleType.SCIENTIFIC)
        self.assertEqual(matched_rule.confidence, 0.85)
        self.assertIn(
            "calificación de confianza media por ausencia de S6.",
            matched_rule.reasoning_template,
        )

    def test_case_5_missing_s2b_produces_zero_point_eight_three_confidence(self) -> None:
        signals = self._build_signals(
            has_sufficient_reference_count=True,
            has_recent_references=False,
            has_methodological_vocabulary=True,
            has_research_intent=True,
            has_evidence_based_contribution=True,
            has_theoretical_justification=True,
        )

        matched_rule = self._rule_table.evaluate(signals)

        self.assertEqual(matched_rule.article_type, ArticleType.SCIENTIFIC)
        self.assertEqual(matched_rule.confidence, 0.83)
        self.assertIn(
            "calificación de confianza media por ausencia de S2b.",
            matched_rule.reasoning_template,
        )

    def _build_signals(self, **kwargs: bool) -> ClassificationSignalsDTO:
        return ClassificationSignalsDTO(**kwargs)
