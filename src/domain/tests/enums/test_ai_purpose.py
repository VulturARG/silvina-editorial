from unittest import TestCase

from src.domain.enums.ai_purpose import AiPurpose


class TestAiPurpose(TestCase):
    def test_members_and_values(self):
        self.assertEqual(AiPurpose.ARTICLE_CLASSIFICATION.value, "article_classification")
        self.assertEqual(AiPurpose.QUALITY_ANALYSIS.value, "quality_analysis")
        self.assertEqual(AiPurpose.EDITORIAL_SUITABILITY.value, "editorial_suitability")

    def test_lookup_by_value(self):
        self.assertIs(AiPurpose("article_classification"), AiPurpose.ARTICLE_CLASSIFICATION)
        self.assertIs(AiPurpose("quality_analysis"), AiPurpose.QUALITY_ANALYSIS)
        self.assertIs(AiPurpose("editorial_suitability"), AiPurpose.EDITORIAL_SUITABILITY)

    def test_invalid_value_raises_value_error(self):
        with self.assertRaises(ValueError):
            AiPurpose("invalid")

    def test_member_count(self):
        self.assertEqual(len(AiPurpose), 3)

    def test_importable_independently(self):
        self.assertIsNotNone(AiPurpose)
