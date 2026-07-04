from unittest import TestCase

from src.domain.classification.classification_rule_table import ClassificationRuleTable
from src.domain.dtos.classification_signals_dto import ClassificationSignalsDTO
from src.domain.enums.article_type import ArticleType


class TestClassificationRuleTablePopularScienceStandard(TestCase):
    def setUp(self) -> None:
        self._rule_table = ClassificationRuleTable()

    def test_case_10_s3_and_s4_not_full_branch(self) -> None:
        signals = self._build_signals(
            has_sufficient_reference_count=False,
            has_recent_references=False,
            has_methodological_vocabulary=True,
            has_research_intent=True,
            has_evidence_based_contribution=False,
            has_theoretical_justification=False,
        )

        matched_rule = self._rule_table.evaluate(signals)

        self.assertEqual(matched_rule.article_type, ArticleType.POPULAR_SCIENCE)
        self.assertIsNone(matched_rule.confidence)
        self.assertIn(
            "No se detectó contribución basada en evidencia (S5 ausente)",
            matched_rule.reasoning_template,
        )

    def test_case_11_s3_and_s5_not_full_branch_not_case_10(self) -> None:
        signals = self._build_signals(
            has_sufficient_reference_count=False,
            has_recent_references=False,
            has_methodological_vocabulary=True,
            has_research_intent=False,
            has_evidence_based_contribution=True,
            has_theoretical_justification=False,
        )

        matched_rule = self._rule_table.evaluate(signals)

        self.assertEqual(matched_rule.article_type, ArticleType.POPULAR_SCIENCE)
        self.assertIsNone(matched_rule.confidence)
        self.assertIn(
            "No se detectó intención investigativa explícita (S4 ausente)",
            matched_rule.reasoning_template,
        )

    def test_case_12_s3_and_s2a_and_s2b(self) -> None:
        signals = self._build_signals(
            has_sufficient_reference_count=True,
            has_recent_references=True,
            has_methodological_vocabulary=True,
            has_research_intent=False,
            has_evidence_based_contribution=False,
            has_theoretical_justification=False,
        )

        matched_rule = self._rule_table.evaluate(signals)

        self.assertEqual(matched_rule.article_type, ArticleType.POPULAR_SCIENCE)
        self.assertIsNone(matched_rule.confidence)
        self.assertIn("respaldo bibliográfico completo (S2a, S2b)", matched_rule.reasoning_template)

    def test_case_13_s3_and_s2a_only(self) -> None:
        signals = self._build_signals(
            has_sufficient_reference_count=True,
            has_recent_references=False,
            has_methodological_vocabulary=True,
            has_research_intent=False,
            has_evidence_based_contribution=False,
            has_theoretical_justification=False,
        )

        matched_rule = self._rule_table.evaluate(signals)

        self.assertEqual(matched_rule.article_type, ArticleType.POPULAR_SCIENCE)
        self.assertIsNone(matched_rule.confidence)
        self.assertIn("cantidad de referencias suficiente (S2a)", matched_rule.reasoning_template)

    def test_case_14_s3_and_s2b_only(self) -> None:
        signals = self._build_signals(
            has_sufficient_reference_count=False,
            has_recent_references=True,
            has_methodological_vocabulary=True,
            has_research_intent=False,
            has_evidence_based_contribution=False,
            has_theoretical_justification=False,
        )

        matched_rule = self._rule_table.evaluate(signals)

        self.assertEqual(matched_rule.article_type, ArticleType.POPULAR_SCIENCE)
        self.assertIsNone(matched_rule.confidence)
        self.assertIn("bibliografía reciente (S2b)", matched_rule.reasoning_template)

    def test_case_15_s3_only(self) -> None:
        signals = self._build_signals(
            has_sufficient_reference_count=False,
            has_recent_references=False,
            has_methodological_vocabulary=True,
            has_research_intent=False,
            has_evidence_based_contribution=False,
            has_theoretical_justification=False,
        )

        matched_rule = self._rule_table.evaluate(signals)

        self.assertEqual(matched_rule.article_type, ArticleType.POPULAR_SCIENCE)
        self.assertIsNone(matched_rule.confidence)
        self.assertIn("Vocabulario metodológico presente (S3)", matched_rule.reasoning_template)

    def test_case_16_s4_and_s5_without_s3_yields_popular_science_not_scientific(self) -> None:
        signals = self._build_signals(
            has_sufficient_reference_count=False,
            has_recent_references=False,
            has_methodological_vocabulary=False,
            has_research_intent=True,
            has_evidence_based_contribution=True,
            has_theoretical_justification=False,
        )

        matched_rule = self._rule_table.evaluate(signals)

        self.assertEqual(matched_rule.article_type, ArticleType.POPULAR_SCIENCE)
        self.assertIsNone(matched_rule.confidence)
        self.assertIn(
            "sin vocabulario metodológico formal (S3 ausente)", matched_rule.reasoning_template
        )

    def test_case_17_s4_only_not_s3_not_s5(self) -> None:
        signals = self._build_signals(
            has_sufficient_reference_count=False,
            has_recent_references=False,
            has_methodological_vocabulary=False,
            has_research_intent=True,
            has_evidence_based_contribution=False,
            has_theoretical_justification=False,
        )

        matched_rule = self._rule_table.evaluate(signals)

        self.assertEqual(matched_rule.article_type, ArticleType.POPULAR_SCIENCE)
        self.assertIsNone(matched_rule.confidence)
        self.assertIn("Intención investigativa detectada (S4)", matched_rule.reasoning_template)

    def test_case_18_s5_only_not_s3_not_s4(self) -> None:
        signals = self._build_signals(
            has_sufficient_reference_count=False,
            has_recent_references=False,
            has_methodological_vocabulary=False,
            has_research_intent=False,
            has_evidence_based_contribution=True,
            has_theoretical_justification=False,
        )

        matched_rule = self._rule_table.evaluate(signals)

        self.assertEqual(matched_rule.article_type, ArticleType.POPULAR_SCIENCE)
        self.assertIsNone(matched_rule.confidence)
        self.assertIn(
            "Contribución basada en evidencia detectada (S5)", matched_rule.reasoning_template
        )

    def _build_signals(self, **kwargs: bool) -> ClassificationSignalsDTO:
        return ClassificationSignalsDTO(**kwargs)
