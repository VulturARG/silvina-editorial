from unittest import TestCase

from src.domain.enums.analysis_dimension import AnalysisDimension
from src.domain.enums.quality_dimension import QualityDimension


class TestQualityDimension(TestCase):
    def test_enum_has_exactly_four_members(self):
        self.assertEqual(len(QualityDimension), 4)

    def test_enum_members_are_clarity_coherence_argumentation_conclusions(self):
        self.assertEqual(QualityDimension.CLARITY.value, "claridad")
        self.assertEqual(QualityDimension.COHERENCE.value, "coherencia")
        self.assertEqual(QualityDimension.ARGUMENTATION.value, "argumentacion")
        self.assertEqual(QualityDimension.CONCLUSIONS.value, "conclusiones")

    def test_quality_dimension_does_not_subclass_analysis_dimension(self):
        self.assertFalse(issubclass(QualityDimension, AnalysisDimension))
        self.assertFalse(issubclass(AnalysisDimension, QualityDimension))

    def test_label_property_returns_spanish_display_name_for_all_members(self):
        self.assertEqual(QualityDimension.CLARITY.label, "Claridad")
        self.assertEqual(QualityDimension.COHERENCE.label, "Coherencia")
        self.assertEqual(QualityDimension.ARGUMENTATION.label, "Argumentación")
        self.assertEqual(QualityDimension.CONCLUSIONS.label, "Conclusiones")

    def test_label_for_returns_spanish_display_name_and_capitalized_fallback_for_unknown_key(
        self,
    ):
        self.assertEqual(QualityDimension.label_for("claridad"), "Claridad")
        self.assertEqual(QualityDimension.label_for("coherencia"), "Coherencia")
        self.assertEqual(QualityDimension.label_for("argumentacion"), "Argumentación")
        self.assertEqual(QualityDimension.label_for("conclusiones"), "Conclusiones")
        self.assertEqual(QualityDimension.label_for("otra_dimension"), "Otra_dimension")
