from unittest import TestCase

from src.domain.dtos.quality_level_thresholds_dto import QualityLevelThresholdsDTO
from src.domain.enums.quality_level import QualityLevel

DEFAULT_THRESHOLDS = QualityLevelThresholdsDTO(
    excellent_threshold=9.0,
    good_threshold=7.0,
    acceptable_threshold=5.0,
    needs_improvement_threshold=3.0,
)


class TestQualityLevel(TestCase):
    def test_members_and_values(self):
        self.assertEqual(QualityLevel.EXCELLENT.value, "Excelente")
        self.assertEqual(QualityLevel.GOOD.value, "Bueno")
        self.assertEqual(QualityLevel.ACCEPTABLE.value, "Aceptable")
        self.assertEqual(QualityLevel.NEEDS_IMPROVEMENT.value, "Requiere mejoras")
        self.assertEqual(QualityLevel.POOR.value, "Deficiente")

    def test_member_count(self):
        self.assertEqual(len(QualityLevel), 5)


class TestQualityLevelFromScore(TestCase):
    def test_score_of_nine_point_zero_returns_excellent(self):
        self.assertEqual(QualityLevel.from_score(9.0, DEFAULT_THRESHOLDS), QualityLevel.EXCELLENT)

    def test_score_just_below_nine_returns_good(self):
        self.assertEqual(QualityLevel.from_score(8.9, DEFAULT_THRESHOLDS), QualityLevel.GOOD)

    def test_score_of_seven_point_zero_returns_good(self):
        self.assertEqual(QualityLevel.from_score(7.0, DEFAULT_THRESHOLDS), QualityLevel.GOOD)

    def test_score_just_below_seven_returns_acceptable(self):
        self.assertEqual(QualityLevel.from_score(6.9, DEFAULT_THRESHOLDS), QualityLevel.ACCEPTABLE)

    def test_score_of_five_point_zero_returns_acceptable(self):
        self.assertEqual(QualityLevel.from_score(5.0, DEFAULT_THRESHOLDS), QualityLevel.ACCEPTABLE)

    def test_score_just_below_five_returns_needs_improvement(self):
        self.assertEqual(
            QualityLevel.from_score(4.9, DEFAULT_THRESHOLDS), QualityLevel.NEEDS_IMPROVEMENT
        )

    def test_score_of_three_point_zero_returns_needs_improvement(self):
        self.assertEqual(
            QualityLevel.from_score(3.0, DEFAULT_THRESHOLDS), QualityLevel.NEEDS_IMPROVEMENT
        )

    def test_score_just_below_three_returns_poor(self):
        self.assertEqual(QualityLevel.from_score(2.9, DEFAULT_THRESHOLDS), QualityLevel.POOR)

    def test_score_of_zero_returns_poor(self):
        self.assertEqual(QualityLevel.from_score(0.0, DEFAULT_THRESHOLDS), QualityLevel.POOR)
